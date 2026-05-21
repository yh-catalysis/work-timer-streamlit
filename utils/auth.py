import streamlit as st
from utils.supabase_client import get_client


def get_session():
    """現在の Supabase セッションを返す。未ログインなら None。"""
    return st.session_state.get("supabase_session")


def get_user():
    """ログイン中ユーザーオブジェクトを返す。未ログインなら None。"""
    session = get_session()
    return session.user if session else None


def get_user_id() -> str | None:
    user = get_user()
    return str(user.id) if user else None


def refresh_session():
    """ページ読み込みごとにクライアントのセッションを再設定する。"""
    session = get_session()
    if not session:
        return
    try:
        client = get_client()
        client.auth.set_session(session.access_token, session.refresh_token)
    except Exception:
        st.session_state.pop("supabase_session", None)


def login(email: str, password: str) -> tuple[bool, str]:
    """メール/パスワードでログイン。成功なら (True, "")、失敗なら (False, エラーメッセージ)。"""
    try:
        client = get_client()
        resp = client.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["supabase_session"] = resp.session
        return True, ""
    except Exception as e:
        return False, str(e)


def logout():
    """ログアウトしてセッションをクリアする。"""
    try:
        get_client().auth.sign_out()
    except Exception:
        pass
    st.session_state.pop("supabase_session", None)
    st.rerun()
