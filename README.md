# Draekhorr WoW Legacy — V1

Personal, unofficial World of Warcraft showcase for **Draekhorr**, Restoration Shaman on **Draenor (EU)**.

**Website:** https://draekhorr.github.io/  
**Repository:** https://github.com/Draekhorr/draekhorr.github.io

> **Versioning:** V1 is the new consolidated project baseline (previous development releases ran through V5.8). Future releases should use V1.1, V1.2, etc. This is a documentation/version-label reset, **not** a change to API versions, game seasons or deployed application code.

## Features

| Area | What the site displays | Source |
| --- | --- | --- |
| Character | Portrait, name, realm, specialization when available, item level | Blizzard Character Profile |
| Lifetime statistics | Total deaths, raid deaths, falling deaths (“Gravity Wins”), achievement points | Blizzard |
| Mythic raids | Active-season progression | Raider.IO |
| Raid History | Older raids by expansion; Mythic preferred, Heroic only where Mythic is unavailable | Blizzard encounters + verified Raider.IO metadata |
| Cutting Edge | Total earned and discreet CE badges beside mapped raids | **Verified Blizzard Cutting Edge achievements only** |
| Mythic+ | Current/previous season scores, dungeon runs, icons, scores and recorded completion times | Raider.IO |
| Warcraft Logs | Boss icons, healing Best parse (integer 0–100, no `%`, truncated), Highest HPS | Warcraft Logs + RPGLogs CDN |
| Monitoring | Health of Blizzard, Raider.IO and Warcraft Logs syncs | GitHub Actions |

The homepage uses the tagline **“RESTORATION SHAMAN SINCE 2005. STILL WAITING FOR A TOP GUILD TO NOTICE.”** The Mounts & Achievements, WoWProgress and separate Cutting Edge card-grid sections have been removed from the displayed site. Achievement points remain in the character banner.

## How automatic updates work

1. `.github/workflows/sync.yml` is scheduled at `0 */6 * * *` (**00:00, 06:00, 12:00, 18:00 UTC**) and also supports manual runs.
2. `scripts/health_monitor.py` runs `scripts/sync_all.py`, checks service success markers, and updates `health_state.json`.
3. The sync script retrieves API data and writes `data.json`; the workflow commits changed files to the repository.
4. GitHub Pages serves the frontend, which reads `data.json` on page load.

GitHub scheduled runs can be delayed or skipped. A successful overall workflow does not prove that every field was refreshed; inspect `WARN`, `OK` and `HEALTH` messages.

### Seasons, expansions and raids

- The current and previous Mythic+ seasons come from Raider.IO's season-specific profile data; the active season is **not** inferred from the highest score.
- On a detected season change, previously saved current raids are archived into `raidProgressionByExpansion.history` before replacement.
- Raids with trustworthy season metadata are classified; unknown raids remain **unclassified** rather than being assigned to the wrong season.
- Historical raid records are retained across updates when possible. Blizzard may omit raids with no recorded kills.
- **Limitation:** Some raid-season mappings remain static fallbacks. Brand-new raids without authoritative metadata are **not guaranteed** to appear automatically immediately after release.
- **CE source of truth:** A full Mythic clear does **not** imply CE. Only a verified Cutting Edge achievement with a known raid mapping produces a CE badge.

## Monitoring and monthly critical alerts

- Three consecutive unsuccessful checks of the **same service** create a critical incident in `health_state.json`.
- A successful subsequent check marks the incident resolved.
- `.github/workflows/monthly-critical-report.yml` runs on the **1st of each month at 09:15 UTC** and creates **one GitHub Issue only if critical incidents were first detected during the preceding month**.
- GitHub can email the Issue assignee depending on their notification settings. **Exactly one email is not guaranteed.** There is no SMTP integration, Gmail password or paid email provider.
- A skipped GitHub Actions run is not detected as a service failure. Partial field failures (for example missing icons) are not yet independently validated.

## Repository structure

```text
/
├── index.html                         # Page markup
├── style.css                          # Styling and responsive layout
├── script.js                          # Frontend data rendering
├── data.json                          # Generated public API data
├── avatar.png                         # Fallback character artwork
├── README.md                          # Project documentation (this file)
├── scripts/
│   ├── sync_all.py                    # Blizzard, Raider.IO, Warcraft Logs sync
│   ├── health_monitor.py              # Health tracking / incident history
│   └── monthly_critical_issue.py      # Monthly issue generator
└── .github/workflows/
    ├── sync.yml                       # 6-hour sync
    └── monthly-critical-report.yml    # Monthly critical-only report
```

Some older diagnostic scripts may also exist; they are not required for the displayed site.

## Setup and operations

**GitHub repository:** `Draekhorr/draekhorr.github.io`, with GitHub Pages publishing the `main` branch root.

Required **GitHub Actions secrets** (never commit actual values):

```text
BLIZZARD_CLIENT_ID
BLIZZARD_CLIENT_SECRET
WARCRAFTLOGS_CLIENT_ID
WARCRAFTLOGS_CLIENT_SECRET
```

Enable **Settings → General → Features → Issues** for monthly reports. Workflows require `contents: write` for data/state commits and `issues: write` for the report. Configure GitHub account **Notifications** for assigned/participating Issues if email alerts are wanted.

**Manual sync:** Actions → **Sync WoW APIs** → **Run workflow**. Review the run's `HEALTH` output and `data.json` / `health_state.json`, then wait for the Pages deployment and refresh the website. Do not replace generated `data.json` with a sample file.

## Data integrity rules

- Missing or failed API values must not be presented as verified zeros or invented results.
- Preserve the last valid data where safe; do not silently relabel a historical score as current.
- Raid progression counts and CE achievements are independent.
- Warcraft Logs HPS comes from `zoneRankings(metric: hps)` / `bestAmount`, not from the parse percentile. A missing or zero amount without a valid ranking should display `—`.
- Boss icons use `https://assets.rpglogs.com/img/warcraft/bosses/<encounterId>-icon.jpg?v=4`; a generated URL does not itself guarantee the image loads.
- Raid Boss Kills lifetime totals were investigated but **not verified** and are **not displayed**. Time Played and Total Healing Done are also omitted because no dependable automatic source was established.

## Known limitations

1. Full automatic discovery of future raid-to-season relationships still depends on reliable provider metadata; unclassified raids require investigation.
2. A real cross-expansion transition has not yet been observed in production, even though a simulated transition was tested.
3. GitHub Issues email delivery depends on notification settings and GitHub behavior.
4. The first monitoring version detects whole-service sync failures, not every partial data regression.
5. Blizzard historical raid counts and old difficulties may be incomplete or require verification.

## Release history

**V1 — Consolidated baseline (October 2026).** Includes all work through the earlier V5.8: character banner and lifetime statistics; verified Cutting Edge badges; historical raid dropdown; dynamic Raider.IO season scores and dungeon cards; Warcraft Logs HPS and boss icons; six-hour API sync; season-transition archiving; API health state; and monthly critical-only GitHub Issues.

Earlier incremental development was tracked as **V4.x–V5.8**. This README intentionally summarizes the current architecture rather than reproducing every intermediate troubleshooting patch.

## Documentation policy

**Maintain this same README on every future release.** Update features, setup, limitations and release history to match the code actually delivered. Do not replace it with patch-only notes. Do not mark a behavior as production-verified unless it has been observed in the deployed workflow/site.

---

*Powered by Windfury, caffeine, and questionable life choices since 2005.*  
*World of Warcraft © Blizzard Entertainment · Unofficial fan project.*
