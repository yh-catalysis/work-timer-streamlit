"""
タイマーページ
- 起動時に進行中レコード（end_time IS NULL）をチェックしてレジューム
- 作業開始: RPC start_work_log（サーバー時刻で start_time を設定）
- 作業終了: RPC complete_work_log（サーバー時刻で end_time を設定）
- 相手先・作業内容が未入力の場合は終了ボタンを非活性化
"""

import time
from datetime import UTC, datetime, timedelta, timezone

import streamlit as st

from utils.auth import get_user_id
from utils.supabase_client import get_client

JST = timezone(timedelta(hours=9))

sb = get_client()
user_id = get_user_id()


# ---- セッション状態の初期化 ----
if "active_log_id" not in st.session_state:
    st.session_state["active_log_id"] = None
if "active_start_time" not in st.session_state:
    st.session_state["active_start_time"] = None
if "timer_initialized" not in st.session_state:
    st.session_state["timer_initialized"] = False


def fetch_active_log() -> dict | None:
    """DB から進行中（end_time IS NULL）レコードを取得する。"""
    resp = (
        sb.table("work_logs").select("id, start_time").eq("user_id", user_id).is_("end_time", "null").limit(1).execute()
    )
    return resp.data[0] if resp.data else None


def fetch_suggestions() -> tuple[list[str], list[str]]:
    """過去入力からユニークな相手先・作業内容リストを取得する。"""
    resp = (
        sb.table("work_logs")
        .select("client, task_detail")
        .eq("user_id", user_id)
        .not_.is_("end_time", "null")
        .execute()
    )
    clients = sorted({r["client"] for r in resp.data if r.get("client")})
    tasks = sorted({r["task_detail"] for r in resp.data if r.get("task_detail")})
    return clients, tasks


# ---- 起動時チェック（初回のみ DB を確認してレジューム） ----
if not st.session_state["timer_initialized"]:
    active = fetch_active_log()
    if active:
        st.session_state["active_log_id"] = active["id"]
        st.session_state["active_start_time"] = datetime.fromisoformat(active["start_time"])
    st.session_state["timer_initialized"] = True


# ================================================================
# UI
# ================================================================
st.title("⏱️ 作業タイマー")
st.divider()

if st.session_state["active_log_id"]:
    # ============================================================
    # 作業中画面
    # ============================================================
    start_time: datetime = st.session_state["active_start_time"]
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=UTC)

    now_utc = datetime.now(UTC)
    elapsed = now_utc - start_time
    total_secs = int(elapsed.total_seconds())
    h, remainder = divmod(total_secs, 3600)
    m, s = divmod(remainder, 60)

    start_jst = start_time.astimezone(JST)
    st.info(f"📌 作業開始: **{start_jst.strftime('%Y/%m/%d %H:%M')}**")
    st.markdown(f'<div class="elapsed">⏱ {h:02d}:{m:02d}:{s:02d}</div>', unsafe_allow_html=True)
    st.write("")

    # 候補一覧を取得
    clients, tasks = fetch_suggestions()

    # ---- 相手先入力 ----
    st.markdown("##### 🏢 相手先")
    client_options = clients + ["＋ 新規入力"]
    client_choice = st.selectbox(
        "相手先",
        client_options if clients else ["＋ 新規入力"],
        index=None,
        placeholder="選択または新規入力...",
        key="client_choice",
        label_visibility="collapsed",
    )
    if client_choice == "＋ 新規入力" or not clients:
        client_val = st.text_input(
            "相手先（新規）", key="client_new", placeholder="例: 株式会社〇〇", label_visibility="collapsed"
        )
    else:
        client_val = client_choice or ""

    # ---- 作業内容入力 ----
    st.markdown("##### 📝 作業内容")
    task_options = tasks + ["＋ 新規入力"]
    task_choice = st.selectbox(
        "作業内容",
        task_options if tasks else ["＋ 新規入力"],
        index=None,
        placeholder="選択または新規入力...",
        key="task_choice",
        label_visibility="collapsed",
    )
    if task_choice == "＋ 新規入力" or not tasks:
        task_val = st.text_area(
            "作業内容（新規）",
            key="task_new",
            placeholder="例: システム設計レビュー",
            height=80,
            label_visibility="collapsed",
        )
    else:
        task_val = task_choice or ""

    st.write("")

    # ---- 終了ボタン（バリデーション） ----
    client_ok = bool(str(client_val or "").strip())
    task_ok = bool(str(task_val or "").strip())
    can_finish = client_ok and task_ok

    if not can_finish:
        st.warning("⚠️ 相手先と作業内容を入力してから終了できます。")

    if st.button("✅ 作業終了", disabled=not can_finish, type="primary", key="finish_btn"):
        with st.spinner("記録を確定しています..."):
            sb.rpc(
                "complete_work_log",
                {
                    "p_log_id": st.session_state["active_log_id"],
                    "p_client": str(client_val).strip(),
                    "p_task_detail": str(task_val).strip(),
                },
            ).execute()
        st.session_state["active_log_id"] = None
        st.session_state["active_start_time"] = None
        st.session_state["timer_initialized"] = False
        st.success("✅ 作業を終了しました！")
        st.balloons()
        time.sleep(1.5)
        st.rerun()

    # 1秒ごとに経過時間を更新
    time.sleep(1)
    st.rerun()

else:
    # ============================================================
    # 新規作業開始画面
    # ============================================================
    st.markdown("### 作業を開始しましょう 🚀")
    st.write("")
    st.write("ボタンを押すと作業時刻が記録されます。")
    st.write("")

    if st.button("🚀 作業開始", type="primary", key="start_btn", width="stretch"):
        with st.spinner("開始しています..."):
            resp = sb.rpc("start_work_log", {}).execute()
            log_id = resp.data

        # DB から実際の start_time を取得
        rec = sb.table("work_logs").select("start_time").eq("id", log_id).single().execute()
        st.session_state["active_log_id"] = log_id
        st.session_state["active_start_time"] = datetime.fromisoformat(rec.data["start_time"])
        st.session_state["timer_initialized"] = True
        st.rerun()
