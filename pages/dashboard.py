"""
ダッシュボードページ
- 月間合計作業時間（metric）
- 相手先別 円グラフ
- 作業内容別 水平棒グラフ
- 日別・相手先別 積み上げ棒グラフ
"""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any, cast

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.auth import get_user_id, refresh_session
from utils.supabase_client import get_client

JST = timezone(timedelta(hours=9))
MONTHS_PER_YEAR = 12

refresh_session()
user_id = get_user_id()
if not user_id:
    st.switch_page("pages/login.py")
    st.stop()

sb = get_client()


@st.cache_data(ttl=30, show_spinner="データを取得中...")
def fetch_records(uid: str, y: int, m: int) -> list[dict[str, Any]]:
    """指定月の完了済みレコードを取得する（JST基準）。"""
    start = datetime(y, m, 1, tzinfo=JST).astimezone(UTC)
    end = (
        datetime(y + 1, 1, 1, tzinfo=JST).astimezone(UTC)
        if m == MONTHS_PER_YEAR
        else datetime(y, m + 1, 1, tzinfo=JST).astimezone(UTC)
    )
    resp = (
        sb.table("work_logs")
        .select("*")
        .eq("user_id", uid)
        .not_.is_("end_time", "null")
        .gte("start_time", start.isoformat())
        .lt("start_time", end.isoformat())
        .order("start_time")
        .execute()
    )
    return [cast("dict[str, Any]", row) for row in (resp.data or []) if isinstance(row, dict)]


# ---- UI ----
st.title("📊 ダッシュボード")
st.divider()

now_jst = datetime.now(JST)
col1, col2 = st.columns(2)
with col1:
    year = st.number_input("年", min_value=2020, max_value=now_jst.year + 1, value=now_jst.year, step=1)
with col2:
    month = st.number_input("月", min_value=1, max_value=12, value=now_jst.month, step=1)

records = fetch_records(user_id, int(year), int(month))

if not records:
    st.info(f"📭 {int(year)}年{int(month)}月の記録はありません。")
    st.stop()

# ---- DataFrame 作成 ----
df = pd.DataFrame(records)
df["start_time"] = pd.to_datetime(df["start_time"], utc=True).dt.tz_convert("Asia/Tokyo")
df["end_time"] = pd.to_datetime(df["end_time"], utc=True).dt.tz_convert("Asia/Tokyo")
df["duration_h"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 3600
df["date"] = df["start_time"].dt.strftime("%m/%d")

# ---- 合計作業時間 ----
total_h_raw = df["duration_h"].sum()
total_h = int(total_h_raw)
total_m = int((total_h_raw - total_h) * 60)

st.metric(
    label=f"📅 {int(year)}年{int(month)}月 合計作業時間",
    value=f"{total_h}時間{total_m}分",
    help=f"{len(records)} 件の記録",
)
st.divider()

COLORS = px.colors.qualitative.Set2

# ---- 相手先別 円グラフ ----
st.subheader("🏢 相手先別 作業時間")
client_df = df.groupby("client")["duration_h"].sum().reset_index()
client_df.columns = ["相手先", "時間"]
fig_pie = px.pie(
    client_df,
    names="相手先",
    values="時間",
    hole=0.35,
    color_discrete_sequence=COLORS,
)
fig_pie.update_traces(textposition="inside", textinfo="percent+label")
fig_pie.update_layout(showlegend=True, margin={"t": 20, "b": 10, "l": 10, "r": 10})
st.plotly_chart(fig_pie, width="stretch")

# ---- 作業内容別 水平棒グラフ ----
st.subheader("📝 作業内容別 作業時間")
task_df = df.groupby("task_detail")["duration_h"].sum().reset_index()
task_df.columns = ["作業内容", "時間 (h)"]
task_df = task_df.sort_values("時間 (h)", ascending=True)
fig_bar = px.bar(
    task_df,
    x="時間 (h)",
    y="作業内容",
    orientation="h",
    color="作業内容",
    color_discrete_sequence=COLORS,
    text_auto=True,
)
fig_bar.update_traces(texttemplate="%{x:.1f}")
fig_bar.update_layout(showlegend=False, margin={"t": 10, "b": 10, "l": 10, "r": 10}, yaxis_title="")
st.plotly_chart(fig_bar, width="stretch")

# ---- 日別・相手先別 積み上げ棒グラフ ----
st.subheader("📅 日別 相手先別 作業時間")
daily_df = df.groupby(["date", "client"])["duration_h"].sum().reset_index()
fig_stack = px.bar(
    daily_df,
    x="date",
    y="duration_h",
    color="client",
    color_discrete_sequence=COLORS,
    labels={"date": "日付", "duration_h": "時間 (h)", "client": "相手先"},
    text_auto=True,
)
fig_stack.update_traces(texttemplate="%{y:.1f}")
fig_stack.update_layout(
    barmode="stack",
    margin={"t": 10, "b": 10, "l": 10, "r": 10},
    xaxis_title="日付",
)
st.plotly_chart(fig_stack, width="stretch")
