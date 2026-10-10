# Draekhorr V4.7 — Warcraft Logs boss visuals

Replace in repository root: `index.html`, `script.js`, `style.css`, `scripts/sync_all.py`.
Do not overwrite `data.json`, secrets, or `.github/workflows/sync.yml`.

The backend attempts Warcraft Logs zone metadata -> encounter journalID -> Blizzard encounter media. These APIs may not expose usable image assets; in that case the frontend shows a neutral placeholder, **not** a fabricated boss image. The sync prints the number of resolved icons and HPS values.

After commit: Actions -> Sync WoW APIs -> Run workflow. Check the `OK warcraftLogs: bosses=..., icons=..., HPS=...` log line. The WCL `amount` field is only treated as HPS if the healing metric query succeeds.
