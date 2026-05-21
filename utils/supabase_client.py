import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    """Supabase クライアントのシングルトン。同一プロセス内で使い回す。"""
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_ANON_KEY", "")
        if not url or not key:
            raise ValueError(
                "環境変数 SUPABASE_URL / SUPABASE_ANON_KEY が未設定です。"
                " .env ファイルまたは Streamlit Secrets を確認してください。"
            )
        _client = create_client(url, key)
    return _client
