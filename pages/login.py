import os

import streamlit as st

from utils.auth import get_google_oauth_url, get_user_id, refresh_session

refresh_session()
if get_user_id():
    st.switch_page("app.py")
    st.stop()

st.title("⏱️ 作業記録アプリ")
st.subheader("ログイン")

oauth_error = st.session_state.pop("oauth_error", None)
if oauth_error:
    st.error(oauth_error)

google_oauth_url = get_google_oauth_url()
supabase_url = os.environ.get("SUPABASE_URL", "").strip().lower()
is_local_target = "127.0.0.1" in supabase_url or "localhost" in supabase_url

if is_local_target:
    # ローカルでは同一タブ遷移でOAuthフローを完結させる
    st.markdown(
        f"""
<a href="{google_oauth_url}" target="_self" style="text-decoration: none;">
    <div style="
        width: 100%;
        min-height: 3.2rem;
        border-radius: 10px;
        background: #2563eb;
        color: white;
        font-weight: 600;
        font-size: 1.05rem;
        display: flex;
        align-items: center;
        justify-content: center;
    ">
        Google でログイン
    </div>
</a>
""",
        unsafe_allow_html=True,
    )
else:
    # Cloudではiframe sandbox制約によりtop navigationが拒否されるため
    # Streamlit標準のリンクボタンで外部遷移する
    st.link_button("Google でログイン", google_oauth_url, type="primary", use_container_width=True)
