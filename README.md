# Draekhorr V4.9.4 — real boss images

Replace only `scripts/sync_all.py` in the repository. Do not replace `data.json`, the website frontend, GitHub secrets or the workflow.

This version obtains `journalID` directly through Warcraft Logs `worldData.encounter(id)` (no zone ID required), then uses Blizzard's `/data/wow/journal-encounter/{id}` creature display references and `/data/wow/media/creature-display/{id}` assets for real artwork. Some encounters may lack assets or their image URLs may be unavailable; in those cases the existing frontend placeholder remains.

After committing, run **Actions → Sync WoW APIs → Run workflow**. Inspect `DIAG WCL direct journal IDs=...` and `OK warcraftLogs: bosses=..., icons=..., HPS=...`. Then check `data.json` for `warcraftLogs.bossParses[].iconUrl`.

This script passed Python syntax checks, but has not been executed with your API secrets. No guarantees that every boss has artwork.
