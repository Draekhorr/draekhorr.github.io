# Draekhorr WoW Legacy

Personal World of Warcraft character showcase for **Draekhorr — Draenor (EU)**.

- Website: https://draekhorr.github.io/
- Repository: https://github.com/Draekhorr/draekhorr.github.io
- Raider.IO: https://raider.io/characters/eu/draenor/Draekhorr
- Warcraft Logs: https://www.warcraftlogs.com/character/eu/draenor/draekhorr

> **Documentation policy:** This is the project's **living README**. On every future change, update this same document **in full**, preserving the project overview, setup, architecture, features, known issues and changelog. Do not replace it with a README that describes only the latest patch. Append a changelog entry and adjust affected sections to match the code actually delivered.

## Project goals

A WoW-themed, mobile-friendly showcase of a Shaman main since 2005. The hero headline is:

> SHAMAN SINCE 2005.  
> STILL WAITING FOR A TOP GUILD TO NOTICE.

The subtitle is: *20+ years of totems, countless raid wipes, and a collection of Cutting Edge achievements. Apparently, my guild application is still pending.*

The site intentionally has **no Twitch or Kick integration**. Current raid progression and Warcraft Logs are displayed together, with Raider.IO directly afterward. Mounts and achievements are side-by-side on desktop and stacked on mobile.

## Feature overview and current status

| Area | Intended behavior | Status / caveat |
| --- | --- | --- |
| Character | Name, race, class, level, item level | Blizzard profile sync implemented |
| Mythic raid progression | Show only current-season raids in main panel | Raider.IO sync implemented; classification of future raids is not fully dynamic |
| Raid history | Compact expansion selector, only one expansion shown at a time | Blizzard historical encounter sync implemented; displayed data depends on API availability and frontend version |
| Raid difficulty | Mythic where available; Heroic only for raids without Mythic | Parser implements priority based on available modes; historical completeness not guaranteed |
| Cutting Edge | Completed achievements, dates and tier count | Blizzard sync implemented; verify IDs, timestamps and raid mapping before claiming tier clears |
| Raider.IO M+ | Current and previous seasonal scores in one row; dungeon cards with Score, Time, and icons | Current/previous lookup implemented; run time uses API `clear_time_ms` when present; dungeon icon URLs are API-provided or explicitly verified, otherwise fallback; future season transitions not yet tested |
| Warcraft Logs | Per-boss healing Best and Highest HPS | WCL HPS metric confirmed in diagnostics; frontend expects `bestPercent` and `highestHps` |
| WCL Best display | Integer from 0–100, truncated (not rounded), no percent sign | Frontend change specified for V4.9.3; check deployed `script.js` |
| WCL boss portraits | Actual boss icons from RPGLogs CDN | V4.9.5 generates image URLs using encounter IDs; individual image availability **not verified** |
| Mounts | Account-wide count and rare highlights | Account-wide count unresolved; character collection count is not equivalent |
| Achievements | Achievement points and rare highlights | Points sync; detailed rare-achievement list still incomplete |
| WoWProgress | Profile / progression link | Not yet populated reliably |
| Auto updates | GitHub Actions every 6 hours | Workflow exists; scheduled runs and commits depend on GitHub Actions configuration |

## Repository layout

```text
/
├── index.html                 # Site markup
├── style.css                  # Theme and responsive styles
├── script.js                  # Fetches data.json and renders the dashboard
├── avatar.png                 # Character artwork
├── data.json                  # Generated public statistics (NO secrets)
├── README.md                  # This cumulative project documentation
├── scripts/
│   └── sync_all.py            # Raider.IO + WCL + Blizzard integrations
└── .github/
    └── workflows/
        └── sync.yml           # Scheduled and manual sync
```

`index.html`, `style.css`, and `script.js` should be in the repository root. Keep `.github/workflows/sync.yml` and `scripts/sync_all.py` in their respective folders.

## API architecture

### Raider.IO

The sync calls the public character API and requests current/previous season data independently. It **does not** infer the active season from the highest historical M+ score. The current-season profile URL is generated from the returned season ID. Known raid slugs have a mapping; new or unknown slugs may remain unclassified until metadata is available. This means automatic season identification is implemented but **automatic classification of every future raid/expansion is not guaranteed**.

Relevant JSON keys: `raiderIo.currentSeason`, `currentSeasonScore`, `previousSeason`, `previousSeasonScore`, `bestRuns`, `raidProgression`, `raidProgressionByExpansion`, `unclassifiedRaidProgression`. Each `bestRuns[]` now includes `score`, `clearTimeMs`, `iconUrl`, `url`, `name`. Run times come from `clear_time_ms` where available; missing times display `—`, never invented. The dungeon icon URL is taken from an API field when present, or an explicitly verified known mapping (currently Temple of Sethraliss). Other icons show a neutral placeholder until their official URLs are verified. Colors are a visual approximation of Raider.IO rarity tiers, not officially verified thresholds. The Ranking tile and TIMED/DEPLETED status have been removed.

### Blizzard API

OAuth client credentials are used by GitHub Actions for character profile, achievements, mounts and `/encounters/raids`. Historical raids are grouped by expansion. The parser prefers Mythic, falling back to Heroic only if the Mythic mode is absent from the response. This is **not proof** of which difficulties were historically offered if the API omits a mode; validate unexpected cases. Raid kills are not necessarily kills achieved while content was current.

`accountWideMountCount: null` means unavailable, not zero. `characterMountCount` is a different metric. Cutting Edge timestamps and IDs need validation, particularly for future-dated or unusual achievements.

### Warcraft Logs V2

OAuth client credentials are used for the GraphQL API. The `zoneRankings(metric: hps)` response supplies per-boss `rankPercent` (Best) and `bestAmount` (HPS). Logs from the October 2026 sync showed sample HPS amounts for Nek'zali, Entombed Sentinels and other bosses. A missing percentile/HPS must display as `—`; zero HPS from a missing ranking is not a confirmed performance.

The frontend consumes `warcraftLogs.bossParses[]` with `name`, `encounterId`, `bestPercent`, `highestHps`, `iconUrl`, `url`. Best parse should display `Math.trunc(Math.max(0, Math.min(100, score)))` with **no `%` sign**. HPS is displayed as a rounded whole-number count with thousands separators.

#### Boss images (V4.9.5)

The script now builds the icon URL using the Warcraft Logs encounter ID:

```text
https://assets.rpglogs.com/img/warcraft/bosses/<encounterId>-icon.jpg?v=4
```

For example, encounter 3470 maps to `https://assets.rpglogs.com/img/warcraft/bosses/3470-icon.jpg?v=4`. The browser loads these assets directly; `script.js` shows a placeholder on image failure. **A non-null `iconUrl` or `icons=10` in workflow logs only confirms URL construction, not HTTP 200 or successful display.** Check the website and network responses. CDN URL conventions could change.

## Setup / deployment

1. Create a **public** GitHub repository named `draekhorr.github.io` under the `Draekhorr` account.
2. In **Settings → Pages**, deploy from `main`, `/ (root)`.
3. In **Settings → Secrets and variables → Actions**, set these repository secrets (never put their values in code, logs, issues or README):

   - `BLIZZARD_CLIENT_ID`
   - `BLIZZARD_CLIENT_SECRET`
   - `WARCRAFTLOGS_CLIENT_ID`
   - `WARCRAFTLOGS_CLIENT_SECRET`

4. Keep `.github/workflows/sync.yml` enabled and ensure its `GITHUB_TOKEN` can commit `data.json` (repository workflow permissions / `contents: write`).
5. For a manual sync: **Actions → Sync WoW APIs → Run workflow → main**.
6. Inspect **sync → Sync WoW Data** logs, then `data.json` in `main`. A green run does not prove every API succeeded; inspect `WARN` and diagnostic lines.
7. Wait for the Pages deployment, visit https://draekhorr.github.io/ and hard-refresh (`Ctrl+F5`). Cache-bust `script.js` in `index.html` if needed.

**Important:** Do not upload an extracted parent folder as an extra directory level. Upload its contents to the repository root, preserving paths. Do not overwrite `data.json` with sample content after a successful sync.

## Current package — V4.9.5

This release replaces **only** `scripts/sync_all.py`. It does not require new credentials or changes to the existing `script.js`, `style.css`, `index.html`, `data.json` or GitHub Actions workflow. After committing, run **Sync WoW APIs** once to regenerate `data.json` with boss icon URLs. Frontend image loading depends on the current deployed JavaScript.

## Validation checklist

- GitHub Actions completes; inspect any `WARN` messages.
- `raiderIo.currentSeasonScore` is the **current** season's value, not historical best.
- Current raid list contains only the active season; historical raids appear via the expansion dropdown.
- Warcraft Logs boss rows contain `bestPercent` and positive `highestHps` when available.
- Best parse shows **81** for `81.009`, not `81%` or `81.0`.
- `iconUrl` is populated for encounters; verify image requests actually succeed in the browser.
- Empty API data displays as unavailable, not fabricated `0` or completed raids.

## Known limitations / next work

1. Boss images are now visible in the deployed site (confirmed by user); monitor CDN changes and fallback behavior.
2. Verify the latest deployed frontend renders HPS and integer Best values correctly.
3. Improve raid slug metadata so newly released raids classify without manual mapping.
4. Test a real season/expansion transition before calling automation fully future-proof.
5. Verify historical raid difficulty and boss counts, and correlate Cutting Edge badges to their raids.
6. Determine a legitimate source for account-wide mount collection and rare mount metadata.
7. Improve rare achievement and WoWProgress coverage.
8. Verify dungeon icon URLs for additional dungeons and confirm run time fields on the next live Raider.IO sync.

## Changelog (cumulative)

| Version | Summary |
| --- | --- |
| Initial / V3 | Personal WoW showcase; raid and Raider.IO placed first; Mounts and Achievements in two columns |
| V4 | Combined Mythic Progression + Warcraft Logs panel, Cutting Edge and WoWProgress sections |
| API Sync V1–V3 | GitHub Actions, Blizzard/WCL/Raider.IO integrations, `data.json`, early season and raid-history classification |
| API Sync V4–V4.2 | Blizzard historical encounters parser; Mythic-first/Heroic fallback; diagnostics and fixes |
| V4.3 | Frontend and backend bundle for historical raid dropdowns |
| V4.4 | Simplified Mythic Progression header, removed redundant labels and duplicate current-season panel |
| V4.5 | Hero copy updated for Shaman since 2005; WCL boss-level Best/HPS table |
| V4.6 | Compact single-expansion Raid History dropdown; initial boss icon support |
| V4.7 | Larger boss text/icons and exploratory icon/HPS lookups |
| V4.8 | Current/previous Raider.IO season discovery; observed 3103.1 vs 3635.2; historical raids sync |
| V4.9 | Warcraft Logs GraphQL diagnostics for missing icons and HPS |
| V4.9.1 | Confirmed WCL `metric: hps` and `bestAmount` values |
| V4.9.2 | Frontend HPS and Best formatting and cache handling |
| V4.9.3 | Best parse display: integer 0–100, truncation, no percent symbol |
| V4.9.4 | Attempted direct WCL encounter-to-Blizzard journal media mapping; diagnostic returned 0/10 journal IDs |
| V4.9.5 | Boss image URLs generated from WCL encounter IDs using RPGLogs CDN; user confirmed images now appear |
| **V5.0** | **Raider.IO UI overhaul:** two scores in one row, Ranking removed, dungeon icons with safe fallback, run Score + actual clear time when API supplies it, no TIMED/DEPLETED badge; complete cumulative README retained |

## Documentation rule for future releases

**Always carry forward and update this entire README** with each ZIP or code patch. Record what changed, what remained untouched, what was actually tested, and what still needs verification. The README must remain a complete onboarding and maintenance guide—not just release notes for the newest version.
