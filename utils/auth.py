import os
import time

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from utils.supabase_client import get_client

COOKIE_REFRESH_TOKEN_KEY = "wt_refresh_token"
COOKIE_REFRESH_EXPIRES_AT_KEY = "wt_refresh_expires_at"


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


def _trusted_device_days() -> int:
    raw = os.environ.get("TRUSTED_DEVICE_DAYS", "30")
    try:
        days = int(raw)
    except ValueError:
        return 30
    return min(max(days, 1), 365)


def _get_cookie_manager() -> EncryptedCookieManager | None:
    secret = os.environ.get("TRUSTED_DEVICE_SECRET", "").strip()
    if not secret:
        return None

    manager = st.session_state.get("_cookie_manager")
    if manager is None:
        manager = EncryptedCookieManager(prefix="work_timer", password=secret)
        st.session_state["_cookie_manager"] = manager
    return manager


def _cookies_ready(manager: EncryptedCookieManager) -> bool:
    try:
        ready = manager.ready()
        if ready:
            st.session_state.pop("_cookie_bootstrap_pending", None)
            return True

        if not st.session_state.get("_cookie_bootstrap_pending"):
            st.session_state["_cookie_bootstrap_pending"] = True
            st.rerun()
        return False
    except Exception:
        return False


def _persist_session_cookie(refresh_token: str) -> None:
    manager = _get_cookie_manager()
    if manager is None or not _cookies_ready(manager):
        return

    expires_at = int(time.time()) + (_trusted_device_days() * 24 * 60 * 60)
    manager[COOKIE_REFRESH_TOKEN_KEY] = refresh_token
    manager[COOKIE_REFRESH_EXPIRES_AT_KEY] = str(expires_at)
    manager.save()


def _clear_session_cookie() -> None:
    manager = _get_cookie_manager()
    if manager is None or not _cookies_ready(manager):
        return

    if COOKIE_REFRESH_TOKEN_KEY in manager:
        del manager[COOKIE_REFRESH_TOKEN_KEY]
    if COOKIE_REFRESH_EXPIRES_AT_KEY in manager:
        del manager[COOKIE_REFRESH_EXPIRES_AT_KEY]
    manager.save()


def refresh_session():
    """ページ読み込みごとにクライアントのセッションを再設定する。"""
    session = get_session()
    client = get_client()

    if not session:
        manager = _get_cookie_manager()
        if manager is None or not _cookies_ready(manager):
            return

        refresh_token = manager.get(COOKIE_REFRESH_TOKEN_KEY)
        expires_at_raw = manager.get(COOKIE_REFRESH_EXPIRES_AT_KEY)
        if not refresh_token:
            return

        if expires_at_raw:
            try:
                if int(expires_at_raw) <= int(time.time()):
                    _clear_session_cookie()
                    return
            except ValueError:
                _clear_session_cookie()
                return

        try:
            refreshed = client.auth.refresh_session(refresh_token)
            if refreshed.session:
                st.session_state["supabase_session"] = refreshed.session
                _persist_session_cookie(refreshed.session.refresh_token)
            else:
                _clear_session_cookie()
        except Exception:
            _clear_session_cookie()
        return

    try:
        client.auth.set_session(session.access_token, session.refresh_token)
    except Exception:
        st.session_state.pop("supabase_session", None)
        _clear_session_cookie()


def login(email: str, password: str) -> tuple[bool, str]:
    """メール/パスワードでログイン。成功なら (True, "")、失敗なら (False, エラーメッセージ)。"""
    try:
        client = get_client()
        resp = client.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["supabase_session"] = resp.session
        if resp.session:
            _persist_session_cookie(resp.session.refresh_token)
        return True, ""
    except Exception as e:
        return False, str(e)


def logout():
    """ログアウトしてセッションをクリアする。"""
    try:
        # local scope only: 他デバイスのセッションは維持する
        get_client().auth.sign_out({"scope": "local"})
    except Exception:
        pass
    st.session_state.pop("supabase_session", None)
    _clear_session_cookie()
    st.rerun()
