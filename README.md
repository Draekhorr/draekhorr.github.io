# DRAEKHORR V2.2 — Raider.IO Historical Seasons

Focused update to the V2 modular project. Only replace `scripts/rio_backfill.py` and `js/mythicplus.js`.

## What changes

- Raider.IO season discovery tries provider season-listing endpoints, preserving all provider-confirmed season identifiers, including special variants.
- Existing archived seasons and current/previous season IDs remain eligible.
- **Only seasons with verified personal scores or runs appear** in the existing expansion-grouped selector.
- Each historical run must carry an explicit matching season ID in metadata or its URL. Missing season metadata is not proof that a run belongs to the requested season.
- Current-season dungeon cards remain the priority for current-season display.
- Raid Logs, Guild Header, HTML, CSS, and the existing 6-hour sync remain unchanged.

## Installation

Upload these two files preserving their paths, commit, then run **Actions → Backfill Raider.IO Mythic Plus → Run workflow**. The existing workflow can be retained. Wait for GitHub Pages to deploy.

## Diagnostics

Check `DIAG RIO discovered season slugs`, `DIAG RIO runs season=... returned=... verified=... unverified=...` and `DIAG RIO historical backfill ...`.

## Limitations

This is **best-effort discovery**, not a guarantee that Raider.IO's public API exposes every season variant visible on its website. Some season-list endpoints may be unavailable or have different response schemas. Those failures are logged, and existing verified archives are preserved. Historical dungeon runs may remain empty when the API does not provide season-verifiable records. The script never fabricates runs or uses current-season runs for historical seasons.

Keep the existing `data.json` and all GitHub Actions workflows. No WCL integration is added to Mythic+.
