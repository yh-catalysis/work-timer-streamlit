import os
from functools import lru_cache

from dotenv import load_dotenv

from supabase import Client, create_client

load_dotenv()


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Supabase クライアントのシングルトン。同一プロセス内で使い回す。"""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        message = (
            "環境変数 SUPABASE_URL / SUPABASE_ANON_KEY が未設定です。"
            " .env ファイルまたは Streamlit Secrets を確認してください。"
        )
        raise ValueError(message)
    return create_client(url, key)
