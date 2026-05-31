"""
タイマーページ
- 起動時に進行中レコード（end_time IS NULL）をチェックしてレジューム
- 作業開始: RPC start_work_log（サーバー時刻で start_time を設定）
- 作業終了: RPC complete_work_log（サーバー時刻で end_time を設定）
- 相手先・作業内容が未入力の場合は終了ボタンを非活性化
"""

import time
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import streamlit as st

from utils.auth import get_user_id, refresh_session
from utils.supabase_client import get_client

JST = timezone(timedelta(hours=9))
RECENT_PILL_COUNT = 3

refresh_session()
sb = get_client()
user_id = get_user_id()
if not user_id:
    st.switch_page("app.py")
    st.stop()


# ---- セッション状態の初期化 ----
if "active_log_id" not in st.session_state:
    st.session_state["active_log_id"] = None
if "active_start_time" not in st.session_state:
    st.session_state["active_start_time"] = None
if "timer_initialized" not in st.session_state:
    st.session_state["timer_initialized"] = False


def fetch_active_log() -> dict[str, Any] | None:
    """DB から進行中（end_time IS NULL）レコードを取得する。"""
    resp = (
        sb.table("work_logs").select("id, start_time").eq("user_id", user_id).is_("end_time", "null").limit(1).execute()
    )
    if not resp.data or not isinstance(resp.data, list):
        return None

    first = resp.data[0]
    if not isinstance(first, dict):
        return None
    return first


def _unique_by_recent(rows: list[dict[str, Any]], field_name: str) -> list[str]:
    """新しい順を保ったまま、空でないユニーク値を返す。"""
    seen: set[str] = set()
    result: list[str] = []
    for row in rows:
        value = str(row.get(field_name) or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _split_recent_and_others(items: list[str]) -> tuple[list[str], list[str]]:
    recent = items[:RECENT_PILL_COUNT]
    others = items[RECENT_PILL_COUNT:]
    return recent, others


def _resolve_input_value(
    typed_value: str,
    selected_recent: str | None,
    selected_other: str | None,
    all_options: list[str],
) -> str:
    typed = typed_value.strip()
    if typed:
        if typed in all_options:
            return typed
        return typed
    if selected_recent:
        return selected_recent
    if selected_other:
        return selected_other
    return ""


def fetch_suggestions() -> tuple[list[str], list[str]]:
    """過去入力から新しい順のユニークな相手先・作業内容リストを取得する。"""
    resp = (
        sb.table("work_logs")
        .select("client, task_detail")
        .eq("user_id", user_id)
        .not_.is_("end_time", "null")
        .order("end_time", desc=True)
        .execute()
    )
    rows = [r for r in resp.data or [] if isinstance(r, dict)]
    clients = _unique_by_recent(rows, "client")
    tasks = _unique_by_recent(rows, "task_detail")
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
    recent_clients, other_clients = _split_recent_and_others(clients)
    recent_tasks, other_tasks = _split_recent_and_others(tasks)

    # ---- 相手先入力 ----
    st.markdown("##### 🏢 相手先")
    if recent_clients:
        client_recent_choice = st.pills(
            "最近の相手先",
            recent_clients,
            selection_mode="single",
            key="client_recent_pill",
            width="stretch",
        )
    else:
        client_recent_choice = None
        st.caption("最近の相手先候補はありません。")

    if other_clients:
        client_other_choice = st.selectbox(
            "その他の相手先を選択",
            other_clients,
            index=None,
            placeholder="候補を検索して選択...",
            key="client_other_select",
            width="stretch",
        )
    else:
        client_other_choice = None
        st.caption("その他の候補はありません。")

    client_typed = st.text_input(
        "新規の相手先を入力",
        key="client_new",
        placeholder="例: 株式会社〇〇",
        width="stretch",
    )

    client_val = _resolve_input_value(
        typed_value=client_typed,
        selected_recent=client_recent_choice,
        selected_other=client_other_choice,
        all_options=clients,
    )

    # ---- 作業内容入力 ----
    st.markdown("##### 📝 作業内容")
    if recent_tasks:
        task_recent_choice = st.pills(
            "最近の作業内容",
            recent_tasks,
            selection_mode="single",
            key="task_recent_pill",
            width="stretch",
        )
    else:
        task_recent_choice = None
        st.caption("最近の作業内容候補はありません。")

    if other_tasks:
        task_other_choice = st.selectbox(
            "その他の作業内容を選択",
            other_tasks,
            index=None,
            placeholder="候補を検索して選択...",
            key="task_other_select",
            width="stretch",
        )
    else:
        task_other_choice = None
        st.caption("その他の候補はありません。")

    task_typed = st.text_area(
        "新規の作業内容を入力",
        key="task_new",
        placeholder="例: システム設計レビュー",
        height=80,
    )

    task_val = _resolve_input_value(
        typed_value=task_typed,
        selected_recent=task_recent_choice,
        selected_other=task_other_choice,
        all_options=tasks,
    )

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
        st.success("✅ 作業を終了しました!")
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
        rec_data = rec.data if isinstance(rec.data, dict) else {}
        start_time_raw = rec_data.get("start_time")
        if not isinstance(start_time_raw, str):
            st.error("開始時刻の取得に失敗しました。再度お試しください。")
            st.stop()

        st.session_state["active_log_id"] = log_id
        st.session_state["active_start_time"] = datetime.fromisoformat(start_time_raw)
        st.session_state["timer_initialized"] = True
        st.rerun()
