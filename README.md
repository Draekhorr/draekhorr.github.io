# Draekhorr — V1.5.7

World of Warcraft character showcase with Blizzard, Raider.IO and Warcraft Logs.

## Data sources

- **Raider.IO:** Mythic+ scores, season navigation, dungeon runs and completion times.
- **Warcraft Logs:** Raid healing parses and HPS only, including available raid history.
- **Blizzard:** Character information, achievements and historical raid progression.

Mythic+ dungeon cards do **not** display Warcraft Logs, healing parses, or HPS. Historical Mythic+ seasons show only verified Raider.IO data; seasons without saved runs show an empty-state message. Expansion-grouped season selection, collapsible navigation, raid logs, guild header and responsive styling are retained.

## Install

Replace `index.html`, `script.js`, `style.css`, `scripts/sync_all.py` and `scripts/wcl_backfill.py` with the files in this package. Keep `data.json`, existing credentials and GitHub Actions workflows. No API sync is required for the visual change. The backend changes stop writing new dungeon-specific WCL archives; existing `dungeonArchive` in `data.json` is not automatically deleted and is ignored by the frontend.

## V1.5.6 — Midnight Season 1 Warcraft Logs

The Warcraft Logs selector retains its expansion groups. Under MIDNIGHT, the former Sporefall-only option is replaced with **Midnight Season 1**, containing the nine raid bosses and their healing statistics transcribed from the supplied Warcraft Logs zone 46 screenshot. Missing parse values remain unavailable (—). The current season and every other archived raid remain unchanged. This is a frontend snapshot, not an API backfill; update the snapshot if the source values change.

## V1.5.7 — Midnight Season 1 metadata repair

Run **Backfill Warcraft Logs** manually after deploying the updated `scripts/wcl_backfill.py`. The script explicitly requests verified WCL zone 46, refreshes its existing archive entry, saves API encounter IDs, validates image response content types for its boss icons, and publishes the result as `season-mn-1`. Existing percent/HPS values are retained if a fresh row omits them. The frontend prefers the new API-backed archive and falls back to the previously supplied screenshot snapshot until the backfill succeeds. Other expansions and Mythic+ remain unchanged.

The backfill requires the existing WCL secrets and a working GitHub Actions workflow. Check logs for `OK WCL Midnight S1 zone=46` and `DIAG WCL backfill`. Icon checks are best-effort: network errors may produce a placeholder until a later run.
