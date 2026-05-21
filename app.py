import streamlit as st
from utils.auth import get_session, refresh_session, logout, get_user

st.set_page_config(
    page_title="作業記録",
    page_icon="⏱️",
    layout="centered",
    initial_sidebar_state="auto",
)

# モバイル最適化 CSS
st.markdown("""
<style>
    /* ボタン大きく */
    .stButton > button {
        width: 100%;
        min-height: 3.2rem;
        font-size: 1.05rem;
        font-weight: 600;
        border-radius: 10px;
        margin-top: 4px;
    }
    /* フォーム入力 */
    .stTextInput > div > input,
    .stSelectbox > div > div {
        min-height: 3rem;
        font-size: 1rem;
    }
    /* メトリクスを中央寄せ */
    [data-testid="metric-container"] {
        text-align: center;
    }
    /* タイマー表示 */
    .elapsed {
        font-size: 2.8rem;
        font-weight: 800;
        color: #2563EB;
        text-align: center;
        letter-spacing: 0.05em;
        padding: 12px 0;
    }
    /* カード風コンテナに余白 */
    [data-testid="stVerticalBlock"] > div:has(> [data-testid="stVerticalBlockBorderWrapper"]) {
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

refresh_session()

# 招待リンク（?code=）があれば未ログインでもパスワード設定ページへ
if st.query_params.get("code") or st.session_state.get("invite_session_exchanged"):
    pages = [
        st.Page("pages/set_password.py", title="パスワード設定", icon="🔐", default=True),
    ]
elif get_session():
    user = get_user()

    # サイドバーにユーザー情報・ログアウト
    with st.sidebar:
        st.markdown(f"**👤** {user.email}")
        if st.button("ログアウト", key="sidebar_logout"):
            logout()
        st.divider()

    pages = [
        st.Page("pages/timer.py",     title="タイマー",         icon="⏱️",  default=True),
        st.Page("pages/dashboard.py", title="ダッシュボード",   icon="📊"),
        st.Page("pages/history.py",   title="履歴",             icon="📋"),
        st.Page("pages/report.py",    title="PDFレポート",      icon="📄"),
    ]
else:
    pages = [
        st.Page("pages/login.py", title="ログイン", icon="🔑", default=True),
    ]

pg = st.navigation(pages)
pg.run()
