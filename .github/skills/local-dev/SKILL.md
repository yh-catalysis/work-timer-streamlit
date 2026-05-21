---
name: local-dev
description: "Local Supabase development workflow for this project. Use when: starting or stopping local Supabase, applying schema changes, creating test users, resetting the database, or checking local connection info."
---

# Local Development Workflow

## Prerequisites

- Docker Desktop running
- `supabase` CLI installed via `mise use -g supabase@latest`

## Start Local Supabase

```bash
supabase start    # first run pulls Docker images (~5-15 min)
supabase status   # show URLs and keys
```

Output includes:
- **Project URL**: `http://127.0.0.1:54321`
- **Publishable** (`sb_publishable_...`) → `SUPABASE_ANON_KEY` in `.env`
- **Secret** (`sb_secret_...`) → used only for admin operations (never committed)
- **Studio**: `http://127.0.0.1:54323`

## Set Up .env

```bash
cp .env.example .env
# Edit .env:
# SUPABASE_URL=http://127.0.0.1:54321
# SUPABASE_ANON_KEY=sb_publishable_...  ← from supabase status
```

## Apply / Reset Schema

```bash
# After editing sql/schema.sql:
cp sql/schema.sql supabase/migrations/20260521000000_init.sql
supabase db reset
```

`supabase db reset` drops and recreates the DB, then re-applies all migrations.
⚠️ All data is lost — use only in development.

## Create a Test User (Admin API)

Replace `<secret_key>` with the Secret key from `supabase status`:

```bash
curl -X POST http://127.0.0.1:54321/auth/v1/admin/users \
  -H "apikey: <secret_key>" \
  -H "Authorization: Bearer <secret_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "email_confirm": true
  }'
```

Or use Studio UI: `http://127.0.0.1:54323` → Authentication → Users → Add user.

## Run the App

```bash
uv run streamlit run app.py
# Open http://localhost:8501
```

## Stop Local Supabase

```bash
supabase stop
```

## Key Notes

- Supabase CLI v2.101.0+ uses `sb_publishable_...` / `sb_secret_...` key format (not `eyJ...` JWT)
- `email_confirm: true` skips email verification for test users
- Local Mailpit (test email inbox): `http://127.0.0.1:54324`
