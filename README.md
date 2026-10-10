# Draekhorr V4.8 — Dynamic season discovery

Replace these files in your GitHub repository:
- `scripts/sync_all.py`
- `script.js`

`index.html` and `style.css` are included as compatible frontend files, but you do not need to replace them if your current V4.7 layout is unchanged.

Do NOT replace `data.json`, `avatar.png`, `.github/workflows/sync.yml`, or GitHub Secrets.

## What changes

The sync requests `mythic_plus_scores_by_season:current` and `mythic_plus_scores_by_season:previous` independently from Raider.IO. It reads the returned season IDs, rather than assuming Midnight Season 2 forever. If Raider.IO does not supply an active-season identifier, it preserves the last known season and logs a warning. If the active season changes but no score is returned, the current score is set to null rather than showing an old score as current.

Previous-season fallback subtracts one only when season number > 1 in the same expansion. At expansion boundaries, the API's previous-season metadata is preferred; if unavailable, the previously stored ID is preserved and must be checked.

Known raid slugs are still mapped to their established seasons. Unknown future raid slugs remain unclassified until an authoritative mapping is available: *fully automatic future raid classification is not yet guaranteed*. Historical Blizzard encounter data is preserved.

## Run and validate

Commit files, then Actions > Sync WoW APIs > Run workflow. Inspect logs for `DIAG RIO` and `OK raiderio`. Check `raiderIo.currentSeason`, `raiderIo.currentSeasonScoreVerified`, and `raidProgressionByExpansion.currentSeason` in `data.json`.

This version has passed Python compilation and JavaScript syntax checks, but has **not** been tested with your GitHub Secrets or live API responses. Raider.IO support for `:current`/`:previous` must be validated by the workflow logs. Do not assume success merely because GitHub Actions turns green.
