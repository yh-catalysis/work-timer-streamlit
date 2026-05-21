import streamlit as st

from utils.auth import login

st.title("⏱️ 作業記録アプリ")
st.subheader("ログイン")

with st.form("login_form"):
    email = st.text_input("メールアドレス", placeholder="email@example.com")
    password = st.text_input("パスワード", type="password", placeholder="••••••••")
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

st.caption("※ アカウント登録は Supabase Auth ダッシュボードから行います。")
