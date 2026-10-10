# Draekhorr API Sync V3

Replace ONLY `scripts/sync_all.py` in the repository. Keep `.github/workflows/sync.yml`, secrets, and existing `data.json` unchanged. Then run **Actions > Sync WoW APIs > Run workflow**.

This version separates explicitly recognized Midnight Season 2 raids from Season 1 raids. `raidProgression` (legacy frontend field) contains current raids only. `raidProgressionByExpansion` provides structured data for future dropdowns. `unclassifiedRaidProgression` retains unknown raid slugs without guessing their season. Other expansions are not populated without verifiable progression data.

The season mapping is currently an explicit allowlist based on your confirmed raids, **not automatic season detection**. Review/update the mapping when seasons change. `tier-mn-1` is left with an unverified display name. Cutting Edge data is unchanged. Existing V4 frontend will only use `raidProgression`; expansion dropdowns require a separate frontend update.

The script has passed Python syntax compilation, but has not been run against your private API credentials. If any API fails, inspect Actions logs. GitHub Actions scheduled sync can overwrite manual edits to data.json.
