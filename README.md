# Draekhorr WoW Legacy — V1.3

An unofficial, automatically updated World of Warcraft character showcase for **Draekhorr**, a Restoration Shaman on **EU–Draenor**.

**Website:** https://draekhorr.github.io/  
**Repository:** https://github.com/Draekhorr/draekhorr.github.io

> **Version:** V1 is the consolidated project label. It does **not** roll back the website, alter game seasons, or change any API integration. Earlier V4–V5 and V1.1.x development notes are consolidated here rather than maintained as separate release entries.

## What the site shows

| Section | Details | Source |
| --- | --- | --- |
| Character | Portrait, guild and Raider.IO guild link, realm, specialization when available, item level | Blizzard / Raider.IO |
| Lifetime stats | Total deaths, raid deaths, falling deaths (“Gravity Wins”), achievement points | Blizzard |
| Mythic raids | Current raid progression and historical raids grouped by expansion | Raider.IO / Blizzard |
| Cutting Edge | Earned achievement count and discreet raid badges | Verified Blizzard achievements |
| Mythic+ | Current/previous season scores, dungeon runs, scores, icons and completion times | Raider.IO |
| Warcraft Logs | Boss portraits, best healing parse and highest HPS | Warcraft Logs / RPGLogs CDN |

The site uses a responsive layout for mobile, tablet, desktop and ultrawide displays. The header shows the current guild when Raider.IO provides it. The Mythic+ section uses the subtitle *“Mythic+ isn't the goal. It's just how I fund my raiding addiction.”* The Mounts & Achievements collection section and WoWProgress section are not displayed.

## Automatic updates

The workflow `.github/workflows/sync.yml` is configured with `0 */6 * * *` (00:00, 06:00, 12:00 and 18:00 UTC), plus manual `workflow_dispatch` runs. It retrieves data, updates `data.json`, and commits changed files for GitHub Pages to serve. The guild sync runs separately in the same workflow. GitHub may delay scheduled runs.

- **Seasons:** Raider.IO determines current and previous seasons; the current score is not inferred from the highest historical score.
- **Raid history:** On a recognized season transition, the sync archives previous current-season raids. New raids require trustworthy provider metadata; unknown raids remain unclassified instead of being assigned incorrectly.
- **Difficulties:** Historical progression prefers Mythic, or Heroic where Mythic is unavailable.
- **Cutting Edge:** A badge appears only for a verified achievement mapped to that raid. Full Mythic progress alone never implies CE.
- **Warcraft Logs:** Best parse is shown as an integer from 0 to 100, without `%` or rounding up; Highest HPS is a separate metric. Missing values remain unavailable rather than invented.

**Known limitation:** A real future expansion transition and discovery of every brand-new raid have not yet been verified in production. Blizzard may omit older encounter records or raids without recorded kills.

## Monitoring and notifications

Health monitoring tracks Blizzard, Raider.IO and Warcraft Logs checks. Three consecutive failures of the same service constitute a critical incident. The monthly workflow (`.github/workflows/monthly-critical-report.yml`) checks for incidents on the first day of the month and creates a GitHub Issue only when qualifying incidents exist. Email delivery depends on GitHub notification settings; it is not guaranteed to be exactly one email.

The monitoring does not detect every partial-data regression or a GitHub scheduled run that never starts.

## Repository layout

```text
index.html                         Page structure
style.css                          Responsive styles
script.js                          Frontend rendering
data.json                          Generated public data
avatar.png                         Fallback character image
scripts/sync_all.py                WoW API sync
scripts/sync_guild.py              Guild sync
scripts/health_monitor.py          Health and incident tracking
scripts/monthly_critical_issue.py  Monthly critical issue report
.github/workflows/sync.yml         Scheduled sync
.github/workflows/monthly-critical-report.yml
README.md                          Project documentation
```

Some optional diagnostic files may exist in the repository.

## Setup and operation

GitHub Pages publishes the repository's `main` branch root. Configure these GitHub Actions secrets (never commit their values):

```text
BLIZZARD_CLIENT_ID
BLIZZARD_CLIENT_SECRET
WARCRAFTLOGS_CLIENT_ID
WARCRAFTLOGS_CLIENT_SECRET
```

Enable repository **Issues** and grant the workflows the required `contents: write` and `issues: write` permissions. Configure GitHub email notifications for assigned or subscribed Issues if monthly alerts are desired.

To run a manual update, open **Actions → Sync WoW APIs → Run workflow**. Check `OK`, `WARN`, `HEALTH` and `GUILD` log messages, then inspect the generated `data.json` and wait for the Pages deployment. Never overwrite production `data.json` with a sample file.

## Data quality and current limitations

- Preserve valid historical records when an API temporarily fails; never substitute old Mythic+ scores for the active season.
- CE badges depend on verified achievements, independently of raid kill counts.
- Warcraft Logs boss icons use the RPGLogs encounter-image URL pattern; a generated URL is not proof that the image exists.
- Lifetime **Time Played**, **Total Healing Done**, and **Raid Boss Kills** are intentionally not shown as verified totals because reliable automatic values were not established.
- Guild membership and raid metadata depend on what the external APIs return.
- Scheduled workflow execution, monitoring, and monthly GitHub email notifications should be verified in the repository after deployment.

## Release and documentation policy

**V1 — Consolidated baseline.** Includes the current character banner, guild header, responsive design, Mythic+ and Warcraft Logs panels, historical raid progression, Cutting Edge verification, six-hour API sync, and critical-failure monitoring.

Future changes should update **this entire README**, including features, setup, limitations and the version label. Do not replace it with a patch-only changelog or claim untested behavior is production-verified.

---

*Powered by Windfury, caffeine, and questionable life choices since 2005.*  
*World of Warcraft © Blizzard Entertainment · Unofficial fan project.*

## Warcraft Logs season archive (V1.2)

The Warcraft Logs panel includes a season dropdown. Choosing a recorded season replaces the boss table rather than adding another section. Boss icons, healing HPS and integer parse scores retain their existing presentation.

The `warcraftLogs.seasonArchive` object in `data.json` stores season-keyed snapshots across successful sync runs. The active season is selected using the Raider.IO current-season identifier. When a season changes, previously stored snapshots remain available; an unsuccessful Warcraft Logs sync does not overwrite the archive.

**Historical coverage limitation:** This version does not retroactively retrieve Warcraft Logs rankings for expansions before the site began recording season snapshots. The dropdown shows only seasons with captured data. Raider.IO season identifiers are used for archive labels, not as Warcraft Logs zone identifiers. To backfill older expansions, a separate verified Warcraft Logs zone/partition discovery integration is required. A saved snapshot represents the most recently synced rankings for that season, not necessarily its final end-of-season rankings.

Files changed: `scripts/sync_all.py`, `script.js`, `index.html`, `style.css`. The existing six-hour GitHub Actions schedule remains unchanged. Commit the files, then manually run Sync WoW APIs once to initialize the first snapshot. The workflow already commits `data.json`.

## Historical Warcraft Logs backfill (V1.3)

The normal 6-hour sync still records the current season. To discover older Warcraft Logs healing parses, run the **Backfill Warcraft Logs** workflow manually (Actions → Backfill Warcraft Logs → Run workflow). It enumerates WCL zones using GraphQL introspection, requests actual `hps` rankings by zone, and merges only nonempty historical results into `data.json`. The existing archive is preserved. It does not infer old HPS from Blizzard raid kills.

The selector in the Warcraft Logs panel now offers **raid / archived season** entries; selecting one replaces the table. Only zones for which the WCL API returns character healing rankings appear. Historical coverage depends on WCL API availability and whether logs exist. The backfill is best-effort and has not been verified against live WCL credentials in this package.

**Diagnostics:** `DIAG WCL backfill discovered zones=...` and `DIAG WCL backfill: added=... existing_or_empty=... errors=...`. If `added=0`, the API may not expose the required zone enumeration/rankings; inspect warnings before attempting another approach. Keep the backfill manual to avoid repeated API-heavy discovery every six hours.


### V1.3.1 — Raid-only Warcraft Logs dropdown

The historical Warcraft Logs dropdown now hides dungeon and Mythic+ zones in the frontend. Archived zone names must match a raid present in the Blizzard raid progression data. The current-season snapshot remains visible. No backend, API, or workflow changes. This is a presentation filter, not a substitute for server-side raid-only filtering; an unmatched legitimate raid may be hidden until Blizzard raid metadata contains its name.


## Mythic+ Warcraft Logs display (V1.4)

The Mythic+ dungeon cards can optionally show **Best healing parse** and **Highest HPS** when the existing `warcraftLogs.seasonArchive` contains a Warcraft Logs zone whose normalized name exactly matches a Raider.IO dungeon. These values are *per dungeon/zone*, not necessarily from the Raider.IO run shown in the card. No missing values are invented. Best parse is truncated to an integer without a percent symbol.

**Important:** This release is a frontend integration only. The current data file may not contain any Mythic+ Warcraft Logs entries, so the cards will remain unchanged until real dungeon-zone records are collected. Existing historical backfill is not guaranteed to retrieve Mythic+ healing rankings; a separate verified backend collector may be needed. The RAID Warcraft Logs dropdown continues to exclude dungeons.

Deployment: replace `index.html`, `script.js`, `style.css`, and `README.md`; no API sync required for this frontend update.


## V1.5 — Unified expansion navigation

Warcraft Logs raid selection now uses expansion-grouped options. Only verified raid zones with real WCL healing data appear. The current season is selected by default.

The Mythic+ section also includes an expansion-grouped season selector. **At present only the current season is selectable**, because the existing `raiderIo.bestRuns` dataset contains current-season runs only. Historical seasons must not be populated with current-season scores/runs.

**Known limitation:** Mythic+ Warcraft Logs metrics are not guaranteed to appear. The existing WCL archive contains raid data; a verified dungeon-healing backend collector is still required. This update does not fabricate HPS or parse values, and does not change API sync workflows.

Deployment: replace `index.html`, `script.js`, `style.css`, and `README.md`.

## V1.5.1 — Guild header regression fix

Restores the dynamic guild name and Raider.IO guild link in the top-left header using `data.json.guild.name` and `data.json.guild.url`. The guild is hidden when data is missing or the URL is invalid. The existing expansion navigation, M+ cards, raid logs, and backend are unchanged. No API sync is needed if `data.json.guild` already exists.

## V1.5.2 — Collapsible Mythic+ season navigation

The Mythic+ expansion/season picker is now placed **after the two score tiles and before the dungeon cards**. It uses a native HTML `<details>` disclosure, so it is **closed on every initial page load** and opens directly below its `SELECT SEASON` heading when clicked. The user can close it again by clicking the heading. The season selection logic and available options are unchanged; historical seasons still require real stored data. Raid Logs and the dynamic guild header are unaffected.

Deployment: replace `index.html`, `style.css`, and `README.md`. No API sync or workflow changes are needed.
