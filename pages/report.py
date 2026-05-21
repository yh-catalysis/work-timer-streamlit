"""
PDFレポートページ
- 対象年月を選択してPDFを生成・ダウンロード
- 日またぎ（深夜作業）は終了時刻を +24h 表記（例: 26:30）
"""

from datetime import UTC, datetime, timedelta, timezone

import streamlit as st

from utils.auth import get_user, get_user_id
from utils.pdf_generator import generate_pdf
from utils.supabase_client import get_client

JST = timezone(timedelta(hours=9))
sb = get_client()
user_id = get_user_id()
user = get_user()


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

if st.button("📄 PDF を生成する", type="primary", width="stretch"):
    y, m = int(year), int(month)

    # 月の範囲（JST → UTC）
    start_utc = datetime(y, m, 1, tzinfo=JST).astimezone(UTC)
    end_utc = (
        datetime(y + 1, 1, 1, tzinfo=JST).astimezone(UTC)
        if m == 12
        else datetime(y, m + 1, 1, tzinfo=JST).astimezone(UTC)
    )

    with st.spinner("データを取得中..."):
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
        records = resp.data

    if not records:
        st.warning(f"📭 {y}年{m}月の完了済み記録はありません。")
    else:
        # ISO文字列を datetime に変換
        for rec in records:
            rec["start_time"] = datetime.fromisoformat(rec["start_time"])
            if rec.get("end_time"):
                rec["end_time"] = datetime.fromisoformat(rec["end_time"])

        with st.spinner("PDF を生成中..."):
            pdf_bytes = generate_pdf(records, y, m, user_email=user.email)

        filename = f"work_report_{y}{m:02d}.pdf"
        st.success(f"✅ {len(records)} 件のレコードから PDF を生成しました。")
        st.download_button(
            label="⬇️ PDF をダウンロード",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            width="stretch",
            type="primary",
        )
