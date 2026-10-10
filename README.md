# Draekhorr V4.9.1 - Warcraft Logs HPS diagnostics

Replace **only** `scripts/sync_all.py` in your GitHub repository. Keep `data.json`, `script.js`, `style.css`, GitHub workflow, and secrets unchanged.

## Changes
- Fixes GraphQL schema inspection missing `variables` argument.
- Reads `bestAmount` rather than nonexistent `amount` for Warcraft Logs HPS rankings, only when an HPS query succeeds and the returned metric is compatible.
- Prints `DIAG WCL sample boss=... bestAmount=... rankPercent=...` for up to eight bosses to compare with Warcraft Logs UI.
- Prints schema fields for Encounter and Zone for investigation of official boss icons. **Icons are not guaranteed yet**; no fake URLs or generated artwork are used.
- Keeps Raider.IO dynamic season and Blizzard historical raid code from V4.9.

## Run
Commit the file and run Actions > Sync WoW APIs > Run workflow. Share lines beginning `DIAG WCL`, `WARN WCL`, and `OK warcraftLogs` (do not share secrets).

This version is not tested with your private API credentials. If HPS numbers differ from the WCL UI, we will adjust the metric and query before treating them as final.
