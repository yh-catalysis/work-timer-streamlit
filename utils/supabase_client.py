import os
from functools import lru_cache

from dotenv import load_dotenv

from supabase import Client, create_client

load_dotenv(override=True)


@lru_cache(maxsize=4)
def _get_client_by_target(url: str, key: str) -> Client:
    """接続先URL/APIキーごとのクライアントをキャッシュする。"""
    return create_client(url, key)


def get_client() -> Client:
    """現在の環境変数に対応する Supabase クライアントを返す。"""
    # .env 編集後のローカル再検証時に古い環境値が残らないよう毎回再読込する
    load_dotenv(override=True)

    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if not url or not key:
        message = (
            "環境変数 SUPABASE_URL / SUPABASE_ANON_KEY が未設定です。"
            " .env ファイルまたは Streamlit Secrets を確認してください。"
        )
        raise ValueError(message)
    return _get_client_by_target(url, key)
