# ⏱️ 作業記録アプリ

Streamlit + Supabase を使用した、スマートフォン対応の作業記録 Web アプリです。

## 機能

| ページ | 機能 |
| -------- | ------ |
| ⏱️ タイマー | ワンタップで作業開始・終了（タイムスタンプはサーバー側で記録・改ざん防止） |
| 📊 ダッシュボード | 月別グラフ（相手先別円グラフ・作業内容別棒グラフ・日別積み上げ） |
| 📋 履歴 | 過去記録の閲覧・削除（値の編集は不可） |
| 📄 PDF レポート | 日またぎ +24h 表記対応の月次レポート出力 |

---

## A. ローカル開発環境でテストする（Supabase CLI + Docker）

本番に最も近い環境でテストできます。

### 前提条件

- Docker が起動していること
- `mise` がインストール済みであること

### 1. Supabase CLI をインストール（mise 経由）

```bash
mise use -g supabase@latest
supabase --version  # 確認
```

### 2. ローカル Supabase を起動

初回はイメージのダウンロードがあるため 5〜15 分かかります。

```bash
supabase init   # 初回のみ（supabase/ ディレクトリを生成）
supabase start  # Docker でローカル Supabase を起動
```

起動が完了すると以下のような情報が表示されます：

```text
Project URL    │ http://127.0.0.1:54321
Publishable    │ sb_publishable_XXXXXXXX...
Secret         │ sb_secret_XXXXXXXX...
```

### 3. スキーマを適用する

```bash
# migrations ディレクトリにスキーマをコピー（初回のみ）
mkdir -p supabase/migrations
cp sql/schema.sql supabase/migrations/{マイグレーション名}.sql

supabase db reset  # マイグレーション適用
```

### 4. 環境変数を設定する

```bash
cp .env.example .env
```

`.env` を `supabase start` で表示された値で書き換えます：

```env
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=sb_publishable_XXXXXXXX...（Publishable の値）
```

### 5. アプリを起動する

```bash
uv run streamlit run app.py
```

ブラウザで `http://localhost:8501` を開き、Google でログインします。

### 6. ローカル Supabase を停止する

```bash
supabase stop
```

---

## B. リモート Supabase でテストする（Free Tier）

### 1. Supabase プロジェクトを作成

[supabase.com](https://supabase.com) でプロジェクトを作成します。

### 2. スキーマを適用する

ダッシュボード > **SQL Editor** で `sql/schema.sql` の内容をすべて貼り付けて実行します。

### 3. 環境変数を設定する

ダッシュボード > **Settings > Data API** からキーを取得します：

```bash
cp .env.example .env
```

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

### 4. アプリを起動する

```bash
uv run streamlit run app.py
```

---

## C. Streamlit Community Cloud にデプロイする

1. このリポジトリを GitHub に push します
2. [share.streamlit.io](https://share.streamlit.io) でリポジトリを連携してデプロイします
3. **Settings > Secrets** に以下を追加します：

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"
```

---

## 技術スタック

- **フロントエンド**: [Streamlit](https://streamlit.io/)
- **データベース**: [Supabase](https://supabase.com/) (PostgreSQL + Row Level Security)
- **グラフ**: [Plotly](https://plotly.com/)
- **PDF 生成**: [ReportLab](https://www.reportlab.com/) (HeiseiKakuGo-W5 日本語フォント)
- **Python バージョン管理**: [uv](https://docs.astral.sh/uv/) + [mise](https://mise.jdx.dev/)

## セキュリティ設計

- **タイムスタンプ改ざん防止**: `start_time` / `end_time` は Supabase の PostgreSQL RPC
  関数内で `now()` を使用。クライアントからの任意の日時送信を受け付けない。
- **データ分離**: Row Level Security (RLS) により、各ユーザーは自分のデータのみ操作可能。
- **編集不可**: 記録済みデータの値変更は UI 上から行えない（削除のみ可能）。
- **認証**: Google OAuth を使用し、メール/パスワード認証フローは廃止。
