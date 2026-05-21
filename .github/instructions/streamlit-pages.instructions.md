---
description: "Use when creating or modifying Streamlit pages in pages/. Covers auth guard, session state, mobile layout, and DB interaction patterns."
applyTo: "pages/**/*.py"
---

# Streamlit Page Conventions

## Required Boilerplate (top of every page)

```python
from utils.auth import get_user_id, refresh_session
from utils.supabase_client import get_client

refresh_session()
user_id = get_user_id()
if not user_id:
    st.switch_page("pages/login.py")
    st.stop()

sb = get_client()
```

## Session State

| Key                 | Type            | Description                                 |
| ------------------- | --------------- | ------------------------------------------- |
| `active_log_id`     | `str` or `None` | ID of in-progress work_log record           |
| `timer_initialized` | `bool`          | Guards one-time DB check on timer page load |
| `supabase_session`  | `Session`       | Raw Supabase auth session object            |

Always check `if "key" not in st.session_state` before initializing.

## DB Interaction

- Call `refresh_session()` at page top — required to restore auth after navigation
- After any INSERT/UPDATE/DELETE that changes displayed state, call `st.rerun()`
- Use `.execute()` and check `.data` for results; handle `None` gracefully

## Mobile-First Layout

- Use `width='stretch'` on all buttons and inputs
- Prefer single-column layouts; avoid multi-column on small screens
- Global mobile CSS is already injected by `app.py` — do not re-inject

## Timer Page Specifics

- `start_work_log()` RPC takes **no arguments** (user_id resolved server-side)
- Disable the "End" button when `client` or `task_detail` is empty:
  ```python
  st.button("終了", disabled=not (client and task_detail))
  ```
- Use `time.sleep(1); st.rerun()` for the live elapsed-time counter
