# DRAEKHORR Forever V2.9.1 — Professions diagnostics and parser fix

This patch changes only `scripts/sync_forever.py`.

## Changes
- Prints counts for `primaries` and `secondaries` and safe field-name diagnostics for primary profession records and tiers.
- Accepts explicit top-level skill totals, or values from a **single** nested tier.
- Does not combine multiple tiers or invent missing skill levels.
- Preserves the last-known-good data when the API does not supply verified professions.
- Leaves the Retail site, Forever frontend, item level, and workflows unchanged.

## Install
Replace `scripts/sync_forever.py` in GitHub, commit, then run **Actions > Sync WoW Forever > Run workflow**.

## Check logs
Look for `DIAG FOREVER professions counts`, `DIAG FOREVER profession[0]`, and `DIAG FOREVER verified primary professions`.
If the count remains zero, share those lines; they show whether the API returns no primary professions or a different skill schema. No full API payload or credentials are printed.
