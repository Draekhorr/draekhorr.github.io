# Draekhorr WoW Legacy

Personal World of Warcraft character showcase for **Draekhorr — Draenor (EU)**.

- Website: https://draekhorr.github.io/
- Repository: https://github.com/Draekhorr/draekhorr.github.io
- Raider.IO: https://raider.io/characters/eu/draenor/Draekhorr
- Warcraft Logs: https://www.warcraftlogs.com/character/eu/draenor/draekhorr

> **Documentation policy:** This is the project's **living README**. On every future change, update this same document **in full**, preserving the project overview, setup, architecture, features, known issues and changelog. Do not replace it with a README that describes only the latest patch. Append a changelog entry and adjust affected sections to match the code actually delivered.

## Project goals

A WoW-themed, mobile-friendly showcase of a Shaman main since 2005. The hero headline is:

> RESTORATION SHAMAN SINCE 2005.  
> STILL WAITING FOR A TOP GUILD TO NOTICE.

The subtitle is: *Started in Vanilla. Still waiting for someone to appreciate my totems.*

The site intentionally has **no Twitch or Kick integration**. A compact Raid Legacy total appears under Raid History in the Mythic Progression panel, alongside Warcraft Logs; Raider.IO follows afterward. The former standalone Cutting Edge card grid and WoWProgress section have been removed. The former Mounts & Achievements section is removed from the website; Blizzard achievement points remain in the character banner.

## Cutting Edge source of truth (V5.1)

Cutting Edge badges are based **only** on Blizzard achievement records where `verified` is `true` and `tierId` has a known raid mapping. Mythic raid progression is independent: a full clear does not imply Cutting Edge, and an earned Cutting Edge does not require all earlier bosses to have been killed on that character. The site displays a single compact total of unique verified Cutting Edge achievement IDs under Raid History within the Mythic Progression panel. Mappings currently cover known Legion, BFA, Shadowlands, Dragonflight and The War Within raids; unmapped achievements remain counted in the total but do not produce a potentially incorrect raid badge. Adding a new raid may require updating the authoritative mapping. No backend change is required for V5.1.

## Feature overview and current status

| Area | Intended behavior | Status / caveat |
| --- | --- | --- |
| Character | Name, race, class, level, item level | Blizzard profile sync implemented |
| Mythic raid progression | Show only current-season raids in main panel | Raider.IO sync implemented; classification of future raids is not fully dynamic |
| Raid history | Compact expansion selector, only one expansion shown at a time | Blizzard historical encounter sync implemented; displayed data depends on API availability and frontend version |
| Raid difficulty | Mythic where available; Heroic only for raids without Mythic | Parser implements priority based on available modes; historical completeness not guaranteed |
| Cutting Edge | Compact total below Raid History; CE badges on raid cards ONLY for verified Blizzard achievement IDs mapped to that raid | Frontend V5.1; currently mapped historical achievements only; unknown/new IDs are not guessed |
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
| **V5.1** | **Raid Legacy UI:** compact verified CE count under Raid History within the Mythic Progression panel, CE badge on historical raid cards only for mapped verified achievement IDs, no inference from kill counts; remove duplicate CE grid and unused WoWProgress section; no API changes |
| **V5.0** | **Raider.IO UI overhaul:** two scores in one row, Ranking removed, dungeon icons with safe fallback, run Score + actual clear time when API supplies it, no TIMED/DEPLETED badge; complete cumulative README retained |

## Documentation rule for future releases

**Always carry forward and update this entire README** with each ZIP or code patch. Record what changed, what remained untouched, what was actually tested, and what still needs verification. The README must remain a complete onboarding and maintenance guide—not just release notes for the newest version.


## V5.2 — Character Profile and Cutting Edge placement

The character identity banner appears **between the homepage hero and Mythic Progression**. It displays the character name, race, class, active specialization when supplied by the Blizzard character profile, realm/region, and equipped item level. The banner uses the official Blizzard character-media portrait when an accessible HTTPS image is returned; otherwise it falls back to the existing `avatar.png`. If Blizzard omits specialization, the website shows the class without guessing the specialization. Item level and character data refresh through the existing GitHub Actions sync. No new secrets are required.

The **single verified Cutting Edge total** is now located **immediately below the Raid History expansion selector/results, inside the left Mythic Raid Progression panel**, above the raid source link. It counts distinct verified achievement IDs; individual CE badges still require explicit achievement-to-raid mapping and never derive from raid kill totals. The old standalone Raid Legacy section above the raids was removed.

Deployment: replace `index.html`, `style.css`, `script.js`, `scripts/sync_all.py` and this **entire** `README.md` in their existing repository locations. Keep `data.json`, `.github/workflows/sync.yml`, GitHub Secrets and `avatar.png`. Commit, run **Actions → Sync WoW APIs**, then wait for GitHub Pages deployment and refresh. Portrait availability depends on Blizzard's media response; a missing image is not an API sync failure.

Changelog: **V5.2** — compact Blizzard-backed character profile banner; automatic item level, best-effort active spec and official portrait with artwork fallback; move CE summary directly under Raid History; retain existing Raider.IO and Warcraft Logs behavior.


## V5.3 — Compact Character Profile (2026-10-11)

- Removed the extra “Still dropping totems since 2005.” tagline from the character banner.
- Reduced the banner height, portrait frame and vertical whitespace before Mythic Progression; removed the intervening top border.
- Changed Blizzard character media preference to the official `avatar` headshot for the compact square frame, falling back to `inset`, `main-raw`, then `main` when unavailable.
- Character portrait remains API-driven. A new **Sync WoW APIs** run is required to refresh `character.portraitUrl` in `data.json`.
- Preserved Mythic Progression, Raider.IO, Warcraft Logs, Cutting Edge, and the rest of the V5.2 features.
- This version does not generate or modify any character artwork.


## V5.4 — Lifetime statistics (diagnostic phase)

The character banner now has a compact two-by-two lifetime statistics area between the character identity and item level: **Time Played**, **Total Deaths**, **Total Healing**, and **Raid Boss Kills**. Unavailable metrics display an em dash (`—`), never an invented number. The portrait, item level, Raid History, Cutting Edge logic, Raider.IO and Warcraft Logs are unchanged.

The Blizzard sync performs a **non-fatal diagnostic** request to `/profile/wow/character/draenor/draekhorr/achievements/statistics`. It logs candidate statistic names, IDs and values without logging credentials. This diagnostic **does not populate** `character.lifetimeStatistics`: the availability and exact meaning of the four requested lifetime counters have not been verified. In particular, the public API may not expose total `/played` time, lifetime healing, or lifetime raid-boss kill counts. Do not conflate a category-specific achievement statistic with a character lifetime total.

After deploying, run **Actions → Sync WoW APIs** once and inspect lines beginning `DIAG Blizzard lifetime` or `WARN Blizzard lifetime`. Confirm IDs, meanings, and units before implementing mapping and enabling numeric display. Do not publish approximations from Warcraft Logs as lifetime totals. GitHub Secrets, workflow and `data.json` should not be overwritten manually.

### Version history addition
- **V5.4:** Compact four-metric character banner; safe Blizzard statistics diagnostics, no unverified lifetime values.


## V5.5 — Lifetime raid kill audit and verified death counters

- The character banner now displays verified Blizzard statistic IDs: total deaths (60), raid deaths (14784), and falling deaths (114). Time played and total healing are removed because no verified automatic source exists.
- Raid Boss Kills includes **every difficulty** (LFR, Normal, Heroic, Mythic, legacy 10/25), and counts repeated kills, not just unique bosses. Dungeon/world bosses and trash are excluded.
- The Blizzard statistics endpoint is parsed into a deduplicated-by-ID candidate audit saved as `raid_kills_audit.json` at the repository root. The audit contains candidate names, IDs, quantities, category paths and a candidate sum.
- **The candidate sum is NOT yet a verified lifetime total.** Keyword filtering is insufficient to guarantee full coverage or eliminate every overlapping statistic. The banner intentionally shows `—` for Raid Boss Kills until the audit is reviewed and a reliable classification strategy is implemented. Do not manually copy the candidate sum into `data.json`.
- Existing Raider.IO, Warcraft Logs, raid progression, and Cutting Edge sync are unchanged. The API secrets are never written to the audit.
- Deployment: replace `index.html`, `script.js`, `scripts/sync_all.py`, and the complete `README.md`. Keep the existing CSS, `data.json`, workflows and secrets. Run the sync, then review `raid_kills_audit.json` and `DIAG Blizzard raid kill audit` output. If the workflow commits only `data.json`, also add `raid_kills_audit.json` to the commit step so the audit is retained.

Changelog: **V5.5** — validated lifetime death counters; raid boss kill audit across all difficulties; no unverified total published.


## V5.5.1 — Raid kill audit fix

Fixed a filter bug: the word `player` previously excluded valid legacy raid counters such as `Icecrown 10 player` and `Icecrown 25 player`. The audit now retains ambiguous kill counters separately under `unclassifiedKillStatistics` for manual review. `candidateSum` is still **not a verified lifetime total**, and the site continues to show `—` until the full set is validated.

**Installation:** Replace only `scripts/sync_all.py` and this complete `README.md`. Run the existing **Sync WoW APIs** workflow. The script generates `raid_kills_audit.json` in the repository root during the workflow, but the file is not necessarily committed or uploaded by the existing workflow. To download it, add this GitHub Actions step **after** the Python sync step to your existing workflow:

```yaml
- name: Upload raid kills audit
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: raid-kills-audit
    path: raid_kills_audit.json
    if-no-files-found: warn
```

Download the artifact from the workflow run summary and share `raid_kills_audit.json` for classification. Do not commit credentials or tokens.


## V5.5.2 — Character banner achievement points

- Replaced the unverified **Raid Boss Kills** tile in the character banner with **Achievement Points**.
- Reads the verified existing top-level `data.json` field `achievementPoints` (Blizzard profile); does not require another API endpoint or manual values.
- Retains **Total Deaths**, **Raid Deaths**, **Gravity Wins**, item level, Raider.IO, Warcraft Logs, Cutting Edge and historical raids.
- Raid kill audit remains diagnostic-only; the banner no longer depends on it.
- Frontend cache-busting script version is `5.5.2`.

**Install:** Replace only root `index.html`, root `script.js`, and root `README.md`. Leave `scripts/sync_all.py`, `data.json`, `style.css`, workflow and secrets untouched. Commit and wait for GitHub Pages deployment; no API sync needed.


## V5.6 — Hero copy, Raid Legacy copy, and footer cleanup

- Removed the entire **Mounts & Achievements** section and its navigation link. The character banner's **Achievement Points** counter remains, sourced from Blizzard. Backend data collection is unchanged.
- Hero headline: **RESTORATION SHAMAN SINCE 2005.** / **STILL WAITING FOR A TOP GUILD TO NOTICE.**
- Hero subtitle: *Started in Vanilla. Still waiting for someone to appreciate my totems.*
- Raid Legacy **THE LONG GAME.** subtitle: *Still chasing Cutting Edge. Unfortunately, my fingers are on cooldown.*
- Outro headline, on one line: **HOME IS WHERE YOUR HEARTHSTONE IS.** Removed the Official Armory button from the outro (the external source links in other sections are unaffected).
- Footer quip: *Powered by Windfury, caffeine, and questionable life choices since 2005.*
- Small attribution: *World of Warcraft © Blizzard Entertainment · Unofficial fan project.*
- Preserved `#status` in the footer for existing sync-status JavaScript; removed obsolete collection DOM updates so missing collection nodes cannot break the page.
- Existing character stats, Raid History, Cutting Edge badges, Warcraft Logs, Raider.IO and automatic API sync are preserved.

**Install:** Replace root `index.html`, `script.js`, `style.css` and this complete `README.md`. Do **not** replace `data.json`, `scripts/sync_all.py`, `.github/workflows/`, avatar assets or GitHub Secrets. Commit, wait for GitHub Pages deployment, then hard refresh. No API sync required.


## V5.6.1 — Responsive character statistics layout

- Fixed character banner layout with explicit responsive grid areas for portrait, identity, lifetime statistics and item level.
- Lifetime statistics now use a flexible 2×2 grid on desktop, four compact columns on medium screens where space allows, and 2×2 on mobile.
- Separated labels from values; numeric values use tabular numerals and thousands separators.
- Fixed Achievement Points binding: frontend reads `achievementPoints` from `data.json`, rather than leaving its value blank.
- No changes to the WoW API sync, raid progression, Warcraft Logs, or Raider.IO.
- Updated script cache version to `5.6.1`.
