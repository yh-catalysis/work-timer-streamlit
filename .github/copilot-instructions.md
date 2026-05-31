# Work Timer App — Project Guidelines

## Architecture

Streamlit multipage app (`st.navigation`) backed by Supabase (PostgreSQL + Auth).

```text
app.py                  # Auth gate + navigation router + global mobile CSS
pages/
  login.py              # Email/password auth
  timer.py              # Work start/stop + resume
  dashboard.py          # Monthly charts (Plotly)
  history.py            # Read-only log list + delete
  report.py             # PDF export
utils/
  supabase_client.py    # Singleton Supabase client (reads .env)
  auth.py               # Session helpers: get_user_id(), refresh_session()
  pdf_generator.py      # ReportLab PDF (HeiseiKakuGo-W5 CIDFont)
sql/schema.sql          # Source of truth for DB schema
supabase/migrations/    # Kept in sync with sql/schema.sql via supabase db reset
```

## Environment & Tooling

- **Python**: 3.13, managed by `uv` (mise → uv → .venv)
- **Run app**: `uv run streamlit run app.py`
- **Supabase CLI**: installed via `mise use -g supabase@latest`
- **Node / npm packages**: mise for Node version, pnpm for package management
  - ⚠️ Never use `npm install -g` or `pnpm add -g` for Supabase
    or other CLI tools. Use mise instead.
- **File creation on this system**: UNC paths (`\\wsl.localhost\...`) are blocked.
  Always write files via WSL:
  `echo '...' | wsl -e bash -ic "python3"`
  or PowerShell here-string piped to `wsl`.

## Key Commands

```bash
uv run streamlit run app.py          # Start app
supabase start                       # Start local Supabase (Docker required)
supabase stop                        # Stop local Supabase
supabase db reset                    # Re-apply all migrations from scratch
supabase status                      # Show local URLs and keys
```

## Supabase / Database Rules

- **Timestamps are tamper-proof**: `start_time` and `end_time` are set only
  inside RPC functions using `now()`.
  Never accept timestamps from the client.
- **RPC functions must use**:
  - `SECURITY INVOKER` (not DEFINER) so RLS applies correctly
  - `SET search_path = ''` to prevent schema injection
  - `REVOKE EXECUTE ON FUNCTION ... FROM anon`
- **RLS policies must use** `(select auth.uid())`.
  Do not use bare `auth.uid()` to avoid per-row re-evaluation.
- **Schema change workflow**:
  Edit `sql/schema.sql`
  → copy to `supabase/migrations/20260521000000_init.sql`
  → `supabase db reset`

## Streamlit Conventions

- All pages call `get_user_id()` from `utils.auth` as the first meaningful line.
  Redirect to login if `None`.
- Session state key for in-progress log ID: `st.session_state["active_log_id"]`
- Timer page uses `start_work_log()` RPC with **no arguments**.
  User identity comes from `auth.uid()` server-side.
- Mobile-first CSS is injected globally in `app.py`.
  Pages should not re-inject it.
- `st.rerun()` after any DB mutation that changes displayed state.

## Python Validation Routine (app.py / pages)

When editing `app.py` or any file under `pages/`,
run both checks below before finishing:

1. **Pylance / Problems check** (type and optional handling)

- In Copilot coding sessions, use `get_errors` for `app.py` and `pages/`.
- Fix all reported `reportOptional*`, `reportArgumentType`,
  and attribute-access issues.

1. **Ruff lint check** (style and static rules)

- Run: `uv run ruff check app.py pages`
- Apply fixes and rerun until clean.

Important: `ruff check` alone is not sufficient.
Ruff mainly catches lint/style rules,
while Pylance catches type-flow issues
(for example optional `None` access and JSON/dict typing mismatches).

## Git

- `.env` is gitignored — never commit it.
- Commit only after the user has completed local testing.
- Never include `Co-authored-by` trailers in commits.
