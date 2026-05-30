import streamlit as st

from utils.auth import get_google_oauth_url, login

st.title("⏱️ 作業記録アプリ")
st.subheader("ログイン")

oauth_error = st.session_state.pop("oauth_error", None)
if oauth_error:
    st.error(oauth_error)

google_oauth_url = get_google_oauth_url()

st.link_button("Google でログイン", google_oauth_url, type="primary", use_container_width=True)

st.divider()

with st.form("login_form"):
    email = st.text_input(
        "メールアドレス",
        placeholder="email@example.com",
        autocomplete="email",
    )
    password = st.text_input(
        "パスワード",
        type="password",
        placeholder="••••••••",
        autocomplete="current-password",
    )
    submitted = st.form_submit_button("ログイン", width="stretch", type="primary")

if submitted:
    if not email.strip() or not password:
        st.warning("メールアドレスとパスワードを入力してください。")
    else:
        with st.spinner("ログイン中..."):
            ok, err = login(email.strip(), password)
        if ok:
            st.rerun()
        else:
            st.error(f"ログインに失敗しました。\n{err}")

st.caption("※ メール/パスワードでのログインも引き続き利用できます。")
