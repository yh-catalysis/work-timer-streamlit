"""
PDFレポートページ
- 対象年月を選択してPDFを生成・ダウンロード
- 日またぎ（深夜作業）は終了時刻を +24h 表記（例: 26:30）
"""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any, cast

import streamlit as st

from utils.auth import get_user, get_user_id, refresh_session
from utils.pdf_generator import generate_pdf
from utils.supabase_client import get_client

JST = timezone(timedelta(hours=9))
MONTHS_PER_YEAR = 12
WorkLogRecord = dict[str, Any]

refresh_session()
user_id = get_user_id()
if not user_id:
    st.switch_page("pages/login.py")
    st.stop()

sb = get_client()
user = get_user()


def _load_month_records(year: int, month: int) -> list[WorkLogRecord]:
    """指定月の完了済みレコードを取得して、扱いやすい dict 配列に正規化する。"""
    start_utc = datetime(year, month, 1, tzinfo=JST).astimezone(UTC)
    end_utc = (
        datetime(year + 1, 1, 1, tzinfo=JST).astimezone(UTC)
        if month == MONTHS_PER_YEAR
        else datetime(year, month + 1, 1, tzinfo=JST).astimezone(UTC)
    )

    resp = (
        sb.table("work_logs")
        .select("*")
        .eq("user_id", user_id)
        .not_.is_("end_time", "null")
        .gte("start_time", start_utc.isoformat())
        .lt("start_time", end_utc.isoformat())
        .order("start_time")
        .execute()
    )

    return [cast("WorkLogRecord", raw_record.copy()) for raw_record in resp.data or [] if isinstance(raw_record, dict)]


def _unique_text_options(records: list[WorkLogRecord], field_name: str) -> list[str]:
    values = {str(record.get(field_name)).strip() for record in records if str(record.get(field_name) or "").strip()}
    return sorted(values)


def _normalize_record_datetimes(records: list[WorkLogRecord]) -> None:
    for record in records:
        start_time = record.get("start_time")
        if isinstance(start_time, str):
            record["start_time"] = datetime.fromisoformat(start_time)

        end_time = record.get("end_time")
        if isinstance(end_time, str):
            record["end_time"] = datetime.fromisoformat(end_time)


def _filter_records(
    records: list[WorkLogRecord],
    selected_clients: list[str],
    selected_tasks: list[str],
) -> list[WorkLogRecord]:
    client_filter = {value.strip() for value in selected_clients if value.strip()}
    task_filter = {value.strip() for value in selected_tasks if value.strip()}

    filtered_records: list[WorkLogRecord] = []
    for record in records:
        client_value = str(record.get("client") or "").strip()
        task_value = str(record.get("task_detail") or "").strip()

        if client_filter and client_value not in client_filter:
            continue
        if task_filter and task_value not in task_filter:
            continue

        filtered_records.append(record)

    return filtered_records


st.title("📄 PDFレポート出力")
st.divider()
st.write("指定した月の作業記録を PDF にまとめてダウンロードできます。")
st.caption("※ 日またぎ作業（深夜0時を越える）は終了時刻を +24h 表記（例: 26:30）で出力します。")
st.write("")

now_jst = datetime.now(JST)
col1, col2 = st.columns(2)
with col1:
    year = st.number_input("年", min_value=2020, max_value=now_jst.year + 1, value=now_jst.year, step=1)
with col2:
    month = st.number_input("月", min_value=1, max_value=12, value=now_jst.month, step=1)

y, m = int(year), int(month)

with st.spinner("データを取得中..."):
    records = _load_month_records(y, m)

if not records:
    st.warning(f"📭 {y}年{m}月の完了済み記録はありません。")
else:
    clients = _unique_text_options(records, "client")
    tasks = _unique_text_options(records, "task_detail")

    st.markdown("##### 🏢 相手先")
    if clients:
        selected_clients = st.pills(
            "相手先",
            clients,
            selection_mode="multi",
            default=clients,
            key="report_client_pills",
            label_visibility="collapsed",
            width="stretch",
        )
    else:
        selected_clients = []
        st.caption("この月に相手先の記録はありません。")

    st.markdown("##### 📝 作業内容")
    if tasks:
        selected_tasks = st.pills(
            "作業内容",
            tasks,
            selection_mode="multi",
            default=tasks,
            key="report_task_pills",
            label_visibility="collapsed",
            width="stretch",
        )
    else:
        selected_tasks = []
        st.caption("この月に作業内容の記録はありません。")

    filtered_records = _filter_records(records, selected_clients, selected_tasks)

    st.write("")
    st.write(f"{len(filtered_records)} 件が出力対象です。")

    if not filtered_records:
        st.warning("選択条件に一致する記録がありません。")
    else:
        _normalize_record_datetimes(filtered_records)

        user_email = ""
        if user is not None and user.email:
            user_email = str(user.email)

        with st.spinner("PDF を生成中..."):
            pdf_bytes = generate_pdf(filtered_records, y, m, user_email=user_email)

        filename = f"work_report_{y}{m:02d}.pdf"
        st.success(f"✅ {len(filtered_records)} 件のレコードから PDF を生成しました。")
        st.download_button(
            label="⬇️ PDF をダウンロード",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            width="stretch",
            type="primary",
        )
