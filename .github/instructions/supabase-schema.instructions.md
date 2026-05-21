---
description: "Use when modifying sql/schema.sql, supabase/migrations/, or any PostgreSQL RLS/RPC code. Covers security patterns and migration sync workflow."
applyTo: ["sql/**", "supabase/migrations/**"]
---
# Supabase Schema Conventions

## RLS Policy Pattern

Always use the subquery form to avoid per-row re-evaluation:

```sql
-- ✅ Correct
USING ((select auth.uid()) = user_id)

-- ❌ Wrong — re-evaluated for every row
USING (auth.uid() = user_id)
```

## RPC Function Pattern

Every RPC function must include all three of these:

```sql
CREATE OR REPLACE FUNCTION public.my_function(...)
RETURNS ...
LANGUAGE plpgsql
SECURITY INVOKER          -- not SECURITY DEFINER
SET search_path = ''      -- prevent schema injection
AS $$
BEGIN
  IF auth.uid() IS NULL THEN
    RAISE EXCEPTION 'Not authenticated';
  END IF;
  -- use auth.uid() directly here (no p_user_id argument)
  ...
END;
$$;

REVOKE EXECUTE ON FUNCTION public.my_function(...) FROM anon;
```

Key rules:
- Never accept a `p_user_id` parameter — always use `auth.uid()` internally
- `SECURITY INVOKER` ensures RLS policies apply to the function's queries
- `SET search_path = ''` prevents search path injection attacks
- Always revoke `EXECUTE` from `anon` role

## Migration Sync Workflow

`sql/schema.sql` is the **source of truth**. After any change:

```bash
cp sql/schema.sql supabase/migrations/20260521000000_init.sql
supabase db reset
```

Both files must always be identical.

## Table Access

- Never grant `SELECT` to `anon` on application tables (prevents GraphQL schema exposure)
- RLS handles per-row access for `authenticated` role
