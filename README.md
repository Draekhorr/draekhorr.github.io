# Draekhorr — V1.5.4

World of Warcraft character showcase with Blizzard, Raider.IO and Warcraft Logs data.

## Setup

Replace `index.html`, `script.js`, `style.css`, `scripts/sync_all.py`, and `scripts/wcl_backfill.py` in the repository. Keep existing `data.json`, credentials, workflows and other scripts.

Run **Backfill Warcraft Logs** manually from GitHub Actions after deployment, then run **Sync WoW APIs**. The existing 6-hour sync remains unchanged.

## Warcraft Logs data handling

The backfill retains WCL zone rankings and additionally indexes a dungeon zone only if its name matches a dungeon in verified Raider.IO best runs. The regular sync preserves this `warcraftLogs.dungeonArchive`. Dungeon healing appears on current-season cards when there is a matching verified zone; it is not claimed to be from the specific Raider.IO run.

**Historical limitations:** WCL zone rankings do not by themselves verify a Mythic+ season or provide historical Raider.IO runs. Season 1 can have a verified score but no cards. No invented values or cross-season HPS are shown. Older dungeon names not present in the current Raider.IO runs cannot yet be reliably classified. Historical coverage requires additional authoritative season/run metadata.

## Navigation

The Mythic+ season selector stays below the score tiles, collapsed initially, with expansion groups. The Guild Header and raid-only Warcraft Logs panel remain unchanged.

## GitHub workflow

If `.github/workflows/wcl-backfill.yml` is absent, upload it manually into that exact path. Existing API secrets are used.
