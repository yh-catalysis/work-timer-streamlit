import streamlit as st

from utils.auth import get_google_oauth_url

st.title("⏱️ 作業記録アプリ")
st.subheader("ログイン")

oauth_error = st.session_state.pop("oauth_error", None)
if oauth_error:
    st.error(oauth_error)

google_oauth_url = get_google_oauth_url()

st.link_button("Google でログイン", google_oauth_url, type="primary", use_container_width=True)

st.caption("※ Google アカウントでのログインのみを使用します。")
