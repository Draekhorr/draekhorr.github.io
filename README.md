# DRAEKHORR Forever V2.9 — Professions

This is an incremental patch to the existing Forever V2.8 site. Only three files change.

- `scripts/sync_forever.py`: makes a best-effort request to the experimental Blizzard Forever `/professions` endpoint, and accepts only explicit primary profession names and skill/max-skill values. If the API does not expose these, the UI shows dashes. No scraping or fabricated values.
- `forever/index.html`: replaces the two kills slots with profession name and skill slots. Level, talents and the separate right-hand Item Level panel remain unchanged.
- `forever/script.js`: renders up to two verified professions from `forever/data.json`.

## Deploy

Upload these three files at their exact paths, commit, and run **Sync WoW Forever** in GitHub Actions. The existing workflow must already provide Blizzard OAuth secrets. Inspect `DIAG FOREVER Blizzard professions status=...` and `DIAG FOREVER verified primary professions=...`.

The Blizzard Forever endpoint and response schema are experimental and may not expose professions. If the request fails, the script retains any previously verified professions for the same character; it does not manufacture values. Retail files are untouched.
