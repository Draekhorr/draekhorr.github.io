# Draekhorr — V1.5.5

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
