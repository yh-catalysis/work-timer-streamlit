"""
履歴ページ
- 過去の作業記録を逆時系列で一覧表示（Read-only）
- 各行に削除ボタン（確認ステップあり）
"""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any, cast

import streamlit as st

from utils.auth import get_user_id, refresh_session
from utils.supabase_client import get_client

JST = timezone(timedelta(hours=9))

refresh_session()
user_id = get_user_id()
if not user_id:
    st.switch_page("app.py")
    st.stop()

sb = get_client()


def to_jst(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(JST)


@st.cache_data(ttl=10, show_spinner="読み込み中...")
def fetch_history(uid: str) -> list[dict[str, Any]]:
    resp = sb.table("work_logs").select("*").eq("user_id", uid).order("start_time", desc=True).execute()
    return [cast("dict[str, Any]", row) for row in (resp.data or []) if isinstance(row, dict)]


# ----------------------------------------------------------------
st.title("📋 作業履歴")
st.divider()

# ---- 削除確認ダイアログ ----
if st.session_state.get("delete_target_id"):
    target_id = st.session_state["delete_target_id"]
    st.error("⚠️ このレコードを削除しますか? この操作は取り消せません。")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("🗑️ 削除する", type="primary", key="confirm_del"):
            sb.table("work_logs").delete().eq("id", target_id).eq("user_id", user_id).execute()
            st.session_state["delete_target_id"] = None
            st.cache_data.clear()
            st.rerun()
    with col_no:
        if st.button("キャンセル", key="cancel_del"):
            st.session_state["delete_target_id"] = None
            st.rerun()
    st.stop()

# ---- 一覧表示 ----
records = fetch_history(user_id)

if not records:
    st.info("📭 まだ作業記録がありません。")
    st.stop()

st.write(f"全 **{len(records)}** 件")

for rec in records:
    start = to_jst(datetime.fromisoformat(rec["start_time"]))
    end_jst = None
    duration_str = "🔄 作業中"

    if rec.get("end_time"):
        end_jst = to_jst(datetime.fromisoformat(rec["end_time"]))
        dur_min = int((end_jst - start).total_seconds() / 60)
        dur_h, dur_m = divmod(dur_min, 60)
        duration_str = f"{dur_h}h{dur_m:02d}m"

    with st.container(border=True):
        col_info, col_del = st.columns([5, 1])

        with col_info:
            # 日付・時間帯
            end_str = end_jst.strftime("%H:%M") if end_jst else "—"
            st.markdown(
                f"**{start.strftime('%Y/%m/%d')}**  "
                f"&nbsp; 🕐 {start.strftime('%H:%M')} → {end_str}"
                f"&nbsp;&nbsp; ⏱ {duration_str}",
            )
            # 相手先・作業内容
            client_str = rec.get("client") or "—"
            task_str = rec.get("task_detail") or "—"
            st.caption(f"🏢 {client_str}　　📝 {task_str}")

        with col_del:
            # 作業中レコードも削除可能（誤操作対応）
            if st.button("🗑️", key=f"del_{rec['id']}", help="このレコードを削除"):
                st.session_state["delete_target_id"] = rec["id"]
                st.rerun()
