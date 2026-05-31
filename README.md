# Work Timer App

[English](#english) | [日本語](#日本語)

---

## English

A mobile-friendly work logging app built with Streamlit + Supabase.

This repository is public under the MIT License.
You can reproduce the same setup with your own Supabase project.

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

Set values based on `supabase start` output:

```env
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=sb_publishable_XXXXXXXX...
TRUSTED_DEVICE_SECRET=replace-with-a-long-random-string
TRUSTED_DEVICE_DAYS=30
```

#### 5. Run app

```bash
uv run streamlit run app.py
```

Open <http://localhost:8501> and sign in with your email/password account.

### Cloud Reproduction (Supabase)

#### 1. Create Supabase project

Create your own project at <https://supabase.com>.

#### 2. Apply schema

Run `sql/schema.sql` in SQL Editor.

#### 3. Create users for sign-in

Create users in Supabase Dashboard > Authentication > Users.
This app assumes account provisioning is handled by the owner/admin.

#### 4. Configure Streamlit Cloud secrets

Use `.streamlit/secrets.toml.example` as template:

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"
TRUSTED_DEVICE_SECRET = "replace-with-a-long-random-string"
TRUSTED_DEVICE_DAYS = "30"
```

### Security Notes

- Timestamp tamper resistance: timestamps are set in DB RPC via now().
- Data isolation: RLS with auth.uid() ensures per-user access only.
- Auth mode: Supabase Email/Password.

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
自分の Supabase プロジェクトで同じ構成を再現できます。

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

`supabase start` の出力を使って設定します。

```env
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=sb_publishable_XXXXXXXX...
TRUSTED_DEVICE_SECRET=十分に長いランダム文字列
TRUSTED_DEVICE_DAYS=30
```

#### 5. アプリ起動

```bash
uv run streamlit run app.py
```

<http://localhost:8501> を開いてメール/パスワードでログインします。

### クラウド再現（Supabase）

#### 1. Supabase プロジェクト作成

<https://supabase.com> でプロジェクトを作成します。

#### 2. スキーマ適用

SQL Editor で `sql/schema.sql` を実行します。

#### 3. ログイン用ユーザーを作成

Supabase Dashboard > Authentication > Users でユーザーを作成します。
このアプリは、オーナー/管理者が事前にアカウントを払い出す運用を想定しています。

#### 4. Streamlit Cloud secrets 設定

`.streamlit/secrets.toml.example` をテンプレートとして使用します。

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"
TRUSTED_DEVICE_SECRET = "replace-with-a-long-random-string"
TRUSTED_DEVICE_DAYS = "30"
```

### セキュリティ設計

- 時刻改ざん防止: 時刻は DB RPC 内の now() で設定
- データ分離: RLS + auth.uid() でユーザー単位に制限
- 認証方式: Supabase Email/Password

### 技術スタック

- Streamlit
- Supabase（PostgreSQL / Auth / RLS）
- Plotly
- ReportLab
- uv + mise
