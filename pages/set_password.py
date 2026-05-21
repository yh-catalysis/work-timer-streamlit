"""
招待リンク受け入れ・パスワード設定ページフロー:
  1. Supabase 招待メールのリンクが ?token_hash=<hash>&type=invite でこのページへリダイレクト
  2. token_hash を verify_otp() でセッションに交換
  3. 新しいパスワードを入力してもらい update_user() で設定
  4. そのままログイン状態でタイマーページへ遷移
"""
import streamlit as st
from utils.supabase_client import get_client

st.title("🔐 パスワードを設定する")

# ── ステップ 1: URL パラメータ取得 ──────────────────────────────
token_hash = st.query_params.get("token_hash")
otp_type   = st.query_params.get("type", "invite")

if not token_hash and not st.session_state.get("invite_session_exchanged"):
    st.error("招待リンクが無効か、期限切れです。管理者に再度招待を依頼してください。")
    st.stop()

# ── ステップ 2: セッション取得（1回だけ実行）────────────────────
if "invite_session_exchanged" not in st.session_state:
    try:
        client = get_client()
        resp = client.auth.verify_otp({"token_hash": token_hash, "type": otp_type})
        st.session_state["supabase_session"] = resp.session
        st.session_state["invite_session_exchanged"] = True
        st.query_params.clear()
    except Exception as e:
        st.error(f"招待トークンの検証に失敗しました: {e}")
        st.stop()

session = st.session_state.get("supabase_session")
if not session:
    st.error("セッションの取得に失敗しました。管理者に再度招待を依頼してください。")
    st.stop()

# ── ステップ 3: パスワード設定フォーム ────────────────────────
st.success(f"ようこそ、{session.user.email} さん！")
st.write("このアプリで使用するパスワードを設定してください。")
st.write("")

with st.form("set_password_form"):
    pw1 = st.text_input("新しいパスワード", type="password")
    pw2 = st.text_input("パスワード（確認）", type="password")
    submitted = st.form_submit_button("パスワードを設定して開始", type="primary", use_container_width=True)

if submitted:
    if not pw1:
        st.warning("パスワードを入力してください。")
    elif pw1 != pw2:
        st.warning("パスワードが一致しません。")
    elif len(pw1) < 8:
        st.warning("パスワードは 8 文字以上で設定してください。")
    else:
        ok = False
        try:
            client = get_client()
            client.auth.set_session(session.access_token, session.refresh_token)
            client.auth.update_user({"password": pw1})
            ok = True
        except Exception as e:
            st.error(f"パスワードの設定に失敗しました: {e}")
        if ok:
            st.success("パスワードを設定しました！アプリを開始します...")
            st.switch_page("pages/timer.py")