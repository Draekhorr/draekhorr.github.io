# Draekhorr V4.9 — Warcraft Logs diagnostics (safe update)

## Installation
Replace **only** `scripts/sync_all.py` in the repository. `script.js` is included for compatibility but is unchanged from V4.8. Keep `data.json`, GitHub Secrets, and `.github/workflows/sync.yml` unchanged.

Then run **Actions > Sync WoW APIs > Run workflow**.

## Why this version is diagnostic
The live V4.8 response contained no zone ID, no image URLs, and no HPS amounts. V4.9 checks additional documented-looking payload keys, logs safe field names from the Warcraft Logs schema, and attempts journal-media mapping **only when a valid zone ID and journal IDs are available**. It never substitutes made-up HPS or unrelated boss pictures.

Read these log lines after the run:
- `DIAG WCL ranking keys=...`
- `DIAG WCL boss keys=...`
- `DIAG WCL encounter keys=...`
- `DIAG WCL schema encounter fields=...`
- `DIAG WCL schema zone fields=...`
- `OK warcraftLogs: bosses=..., icons=..., HPS=...`

**If icons/HPS remain zero, this release does not fix them yet.** The schema output is needed to implement a verified source for the media and HPS metrics. Raider.IO and Blizzard sync logic is carried forward unchanged from V4.8.
