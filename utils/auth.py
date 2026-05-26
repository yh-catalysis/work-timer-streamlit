import os
import time
from contextlib import suppress

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from supabase import AuthApiError, AuthRetryableError, AuthUnknownError
from utils.supabase_client import get_client

AUTH_EXCEPTIONS = (AuthApiError, AuthRetryableError, AuthUnknownError, ValueError)
COOKIE_REFRESH_TOKEN_KEY = "wt_refresh_token"  # noqa: S105
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
    with suppress(Exception):
        ready = manager.ready()
        if ready:
            st.session_state.pop("_cookie_bootstrap_pending", None)
            return True

        if not st.session_state.get("_cookie_bootstrap_pending"):
            st.session_state["_cookie_bootstrap_pending"] = True
            st.rerun()
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


def _restore_session_from_cookie(client) -> None:
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

    with suppress(*AUTH_EXCEPTIONS):
        refreshed = client.auth.refresh_session(refresh_token)
        if refreshed.session:
            st.session_state["supabase_session"] = refreshed.session
            _persist_session_cookie(refreshed.session.refresh_token)
        else:
            _clear_session_cookie()
        return

    _clear_session_cookie()


def _sync_existing_session(client, session) -> None:
    with suppress(*AUTH_EXCEPTIONS):
        client.auth.set_session(session.access_token, session.refresh_token)
        return

    st.session_state.pop("supabase_session", None)
    _clear_session_cookie()


def refresh_session():
    """ページ読み込みごとにクライアントのセッションを再設定する。"""
    session = get_session()
    client = get_client()

    if session:
        _sync_existing_session(client, session)
        return

    _restore_session_from_cookie(client)


def login(email: str, password: str) -> tuple[bool, str]:
    """メール/パスワードでログイン。成功なら (True, "")、失敗なら (False, エラーメッセージ)。"""
    try:
        client = get_client()
        resp = client.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["supabase_session"] = resp.session
        if resp.session:
            _persist_session_cookie(resp.session.refresh_token)
    except AUTH_EXCEPTIONS as e:
        return False, str(e)

    return True, ""


def logout():
    """ログアウトしてセッションをクリアする。"""
    with suppress(*AUTH_EXCEPTIONS):
        # local scope only: 他デバイスのセッションは維持する
        get_client().auth.sign_out({"scope": "local"})
    st.session_state.pop("supabase_session", None)
    _clear_session_cookie()
    st.rerun()
