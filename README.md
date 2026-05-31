# Work Timer App

[English](#english) | [日本語](#日本語)

---

## English

A mobile-friendly work logging app built with Streamlit + Supabase.

This repository is public under the MIT License.
You can reproduce the same setup with your own Supabase and Google Cloud projects.

Single-user private operation is assumed. Public sign-up is intentionally not provided.

### Features

| Page | Description |
| --- | --- |
| Timer | Start/stop work with server-side timestamps |
| Dashboard | Monthly charts (client/task/day breakdown) |
| History | Read-only log list and delete |
| PDF Report | Monthly PDF export with day-overflow handling |

### Local Development (Supabase CLI + Docker)

#### Prerequisites

- Docker
- mise
- uv

#### 1. Install Supabase CLI

```bash
mise use -g supabase@latest
supabase --version
```

#### 2. Start local Supabase

```bash
supabase init
supabase start
```

#### 3. Apply schema

```bash
mkdir -p supabase/migrations
cp sql/schema.sql supabase/migrations/20260521000000_init.sql
supabase db reset
```

#### 4. Configure environment variables

```bash
cp .env.example .env
```

Set values based on `supabase start` output and your Google OAuth client:

```env
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=sb_publishable_XXXXXXXX...
TRUSTED_DEVICE_SECRET=replace-with-a-long-random-string
TRUSTED_DEVICE_DAYS=30
OAUTH_REDIRECT_TO=http://127.0.0.1:8501
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

#### 5. Run app

```bash
uv run streamlit run app.py
```

Open <http://localhost:8501> and click Google sign-in.

### Cloud Reproduction (Supabase + Google)

#### 1. Create Supabase project

Create your own project at <https://supabase.com>.

#### 2. Apply schema

Run `sql/schema.sql` in SQL Editor.

#### 3. Configure Google OAuth

1. Create OAuth client in Google Auth Platform (Web application).
2. Add authorized redirect URIs:
   - `https://<your-project-ref>.supabase.co/auth/v1/callback`
   - `http://127.0.0.1:54321/auth/v1/callback`
3. Keep OAuth app in Testing mode and add your account
   to Test users if private use.
4. In Supabase Dashboard > Authentication > Providers > Google, enable and set
   Client ID / Client Secret.

#### 4. Configure Streamlit Cloud secrets

Use `.streamlit/secrets.toml.example` as template:

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"
TRUSTED_DEVICE_SECRET = "replace-with-a-long-random-string"
TRUSTED_DEVICE_DAYS = "30"
```

Do not set `OAUTH_REDIRECT_TO` on Streamlit Cloud.
It is only for local OAuth verification.

### Desktop PWA (Chrome) notes

- If you install the app as a desktop PWA on Windows + Chrome,
  Google OAuth may open a separate browser tab/window.
- This behavior depends on browser/PWA OAuth handling and can differ from Android.
- Recommended operation for desktop: start login in the same app window,
  and if another app window appears after OAuth,
  continue in the authenticated one.
- Keep using one canonical app URL to reduce duplicate app-window launches.

### Security Notes

- Timestamp tamper resistance: timestamps are set in DB RPC via now().
- Data isolation: RLS with auth.uid() ensures per-user access only.
- Auth mode: Google OAuth only (email/password flow removed).

### Tech Stack

- Streamlit
- Supabase (PostgreSQL, Auth, RLS)
- Plotly
- ReportLab
- uv + mise

---

## 日本語

Streamlit + Supabase を使用した、スマートフォン対応の作業記録 Web アプリです。

このリポジトリは MIT License で公開されています。
自分の Supabase / Google Cloud プロジェクトで同じ構成を再現できます。

想定運用は単一ユーザーです。公開向けの新規ユーザー登録機能は意図的に実装していません。

### 機能

| ページ | 機能 |
| --- | --- |
| タイマー | ワンタップで作業開始・終了（時刻はサーバー側で記録） |
| ダッシュボード | 月別グラフ（相手先・作業内容・日別） |
| 履歴 | 過去記録の閲覧・削除 |
| PDFレポート | 月次PDF出力（+24h表記対応） |

### ローカル開発（Supabase CLI + Docker）

#### 前提

- Docker
- mise
- uv

#### 1. Supabase CLI を導入

```bash
mise use -g supabase@latest
supabase --version
```

#### 2. ローカル Supabase 起動

```bash
supabase init
supabase start
```

#### 3. スキーマ適用

```bash
mkdir -p supabase/migrations
cp sql/schema.sql supabase/migrations/20260521000000_init.sql
supabase db reset
```

#### 4. 環境変数設定

```bash
cp .env.example .env
```

`supabase start` の出力と Google OAuth クライアント情報を使って設定します。

```env
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=sb_publishable_XXXXXXXX...
TRUSTED_DEVICE_SECRET=十分に長いランダム文字列
TRUSTED_DEVICE_DAYS=30
OAUTH_REDIRECT_TO=http://127.0.0.1:8501
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

#### 5. アプリ起動

```bash
uv run streamlit run app.py
```

<http://localhost:8501> を開いて Google ログインを実行します。

### クラウド再現（Supabase + Google）

#### 1. Supabase プロジェクト作成

<https://supabase.com> でプロジェクトを作成します。

#### 2. スキーマ適用

SQL Editor で `sql/schema.sql` を実行します。

#### 3. Google OAuth 設定

1. Google Auth Platform で OAuth Client（Web application）を作成
2. Authorized redirect URIs に以下を追加
   - `https://<your-project-ref>.supabase.co/auth/v1/callback`
   - `http://127.0.0.1:54321/auth/v1/callback`
3. 自分専用で使う場合は Testing のまま Test users を登録
4. Supabase Dashboard > Authentication > Providers > Google で有効化し、
   Client ID / Client Secret を設定

#### 4. Streamlit Cloud secrets 設定

`.streamlit/secrets.toml.example` をテンプレートとして使用します。

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"
TRUSTED_DEVICE_SECRET = "replace-with-a-long-random-string"
TRUSTED_DEVICE_DAYS = "30"
```

Streamlit Cloud では `OAUTH_REDIRECT_TO` を設定しないでください。
この変数はローカルOAuth検証専用です。

### PC版PWA（Chrome）利用時の注意

- Windows + Chrome のデスクトップPWAでは、Google OAuth時に別タブ/別ウィンドウが開くことがあります。
- この挙動はブラウザとPWAのOAuth処理に依存し、Androidとは動きが異なる場合があります。
- 運用上は、認証後にログイン済みのウィンドウ側を継続利用してください。
- 入口URLを1つに統一すると、アプリウィンドウの重複起動を減らせます。

### セキュリティ設計

- 時刻改ざん防止: 時刻は DB RPC 内の now() で設定
- データ分離: RLS + auth.uid() でユーザー単位に制限
- 認証方式: Google OAuth のみ（メール/パスワード廃止）

### 技術スタック

- Streamlit
- Supabase（PostgreSQL / Auth / RLS）
- Plotly
- ReportLab
- uv + mise
