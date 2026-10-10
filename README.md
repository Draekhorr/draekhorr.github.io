# Draekhorr V4.5 — Homepage + Warcraft Logs table

Upload **index.html**, **script.js**, **style.css**, and **scripts/sync_all.py** to the same paths in your GitHub repository. Do not overwrite data.json, avatar.png, or .github/workflows/sync.yml.

The hero title and subtitle have been updated. The Warcraft Logs panel now shows Boss / Best % / Highest HPS and removes average metrics.

The sync script attempts a healing-specific Warcraft Logs query (`zoneRankings(metric: hps)`). If that argument is rejected, it falls back to the existing query and leaves HPS as — unless a previously verified HPS value exists. An `amount` is treated as HPS only for a successful healing-specific query. **API-specific semantics and whether amount is truly highest HPS require validation in GitHub Actions.**

After committing, run Actions > Sync WoW APIs. Check for `OK warcraftLogs (... healing metric: True)` or `WARN WCL healing query unavailable`. If unavailable, share that log to adapt the GraphQL query.
