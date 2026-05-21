-- =============================================================
-- work_logs テーブル定義
-- =============================================================
CREATE TABLE IF NOT EXISTS public.work_logs (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  start_time  timestamptz NOT NULL DEFAULT now(),
  end_time    timestamptz,
  client      text,
  task_detail text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- インデックス（ユーザー別・日時検索の高速化）
CREATE INDEX IF NOT EXISTS idx_work_logs_user_id    ON public.work_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_work_logs_start_time ON public.work_logs (start_time DESC);

-- =============================================================
-- Row Level Security (RLS)
-- =============================================================
ALTER TABLE public.work_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "select_own_logs"
  ON public.work_logs FOR SELECT
  USING ((select auth.uid()) = user_id);

CREATE POLICY "insert_own_logs"
  ON public.work_logs FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "update_own_logs"
  ON public.work_logs FOR UPDATE
  USING ((select auth.uid()) = user_id);

CREATE POLICY "delete_own_logs"
  ON public.work_logs FOR DELETE
  USING ((select auth.uid()) = user_id);

-- authenticated ロールに操作権限を明示付与（Supabase Cloud ではデフォルト権限が自動付与されないことがある）
GRANT SELECT, INSERT, UPDATE, DELETE ON public.work_logs TO authenticated;

-- anon ロールからは全権限を剥奪（未ログインユーザーはアクセス不可 / GraphQL スキーマ露出も防ぐ）
REVOKE ALL ON public.work_logs FROM anon;

-- =============================================================
-- RPC: 作業開始 -- start_time は DB の now() で設定（改ざん防止）
-- SECURITY INVOKER: 呼び出しユーザーの権限で実行（RLS が正しく機能する）
-- SET search_path = '': スキーマインジェクション攻撃を防止
-- =============================================================
CREATE OR REPLACE FUNCTION public.start_work_log()
RETURNS uuid
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
  v_id      uuid;
  v_user_id uuid;
BEGIN
  v_user_id := auth.uid();

  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'Not authenticated';
  END IF;

  -- すでに進行中のレコードがある場合は新規作成しない（冪等性）
  SELECT id INTO v_id
    FROM public.work_logs
   WHERE user_id = v_user_id
     AND end_time IS NULL
   LIMIT 1;

  IF v_id IS NOT NULL THEN
    RETURN v_id;
  END IF;

  INSERT INTO public.work_logs (user_id, start_time)
  VALUES (v_user_id, now())
  RETURNING id INTO v_id;

  RETURN v_id;
END;
$$;

-- anon ロールから RPC の実行権限を剥奪
REVOKE EXECUTE ON FUNCTION public.start_work_log() FROM anon;

-- =============================================================
-- RPC: 作業終了 -- end_time は DB の now() で設定（改ざん防止）
-- SECURITY INVOKER: 呼び出しユーザーの権限で実行（RLS が正しく機能する）
-- SET search_path = '': スキーマインジェクション攻撃を防止
-- =============================================================
CREATE OR REPLACE FUNCTION public.complete_work_log(
  p_log_id      uuid,
  p_client      text,
  p_task_detail text
)
RETURNS void
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
BEGIN
  IF auth.uid() IS NULL THEN
    RAISE EXCEPTION 'Not authenticated';
  END IF;

  UPDATE public.work_logs
     SET end_time    = now(),
         client      = p_client,
         task_detail = p_task_detail
   WHERE id      = p_log_id
     AND user_id = auth.uid()
     AND end_time IS NULL;
END;
$$;

-- anon ロールから RPC の実行権限を剥奪
REVOKE EXECUTE ON FUNCTION public.complete_work_log(uuid, text, text) FROM anon;
