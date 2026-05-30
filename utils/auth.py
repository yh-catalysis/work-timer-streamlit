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


def get_google_oauth_url() -> str:
    """Google OAuth ログイン用の認可URLを返す。"""
    client = get_client()
    response = client.auth.sign_in_with_oauth({"provider": "google"})
    return response.url


def exchange_oauth_code(auth_code: str) -> None:
    """OAuth コールバックの認可コードをセッションに交換する。"""
    client = get_client()
    response = client.auth.exchange_code_for_session({"auth_code": auth_code})
    if response.session:
        st.session_state["supabase_session"] = response.session
        _persist_session_cookie(response.session.refresh_token)


def handle_oauth_callback() -> bool:
    """OAuth の戻りURLが開かれた場合にコードを交換する。成功時は True。"""
    oauth_error = st.query_params.get("error")
    if isinstance(oauth_error, list):
        oauth_error = oauth_error[0] if oauth_error else None
    if oauth_error:
        st.session_state["oauth_error"] = oauth_error
        st.query_params.clear()
        st.rerun()

    auth_code = st.query_params.get("code")
    if isinstance(auth_code, list):
        auth_code = auth_code[0] if auth_code else None

    if not auth_code:
        return False

    try:
        exchange_oauth_code(auth_code)
    except AUTH_EXCEPTIONS as exc:
        st.session_state["oauth_error"] = str(exc)
        st.query_params.clear()
        st.rerun()

    st.query_params.clear()
    st.rerun()
    return True


def logout():
    """ログアウトしてセッションをクリアする。"""
    with suppress(*AUTH_EXCEPTIONS):
        # local scope only: 他デバイスのセッションは維持する
        get_client().auth.sign_out({"scope": "local"})
    st.session_state.pop("supabase_session", None)
    _clear_session_cookie()
    st.rerun()
