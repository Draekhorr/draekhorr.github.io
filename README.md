# Draekhorr V4.2 Frontend Fix

Upload **index.html**, **script.js**, and **style.css** to the repository root, replacing the existing files. `avatar.png` is included only for convenience. Do not overwrite your live `data.json`, `.github/workflows/sync.yml`, or `scripts/sync_all.py`.

This version shows only The Venomous Abyss and The Tidebound Grotto under current Midnight Season 2; Sporefall and Tier MN 1 appear in the Midnight > Season 1 dropdown. Unknown raid names are grouped under Unclassified raids rather than incorrectly assigned. Current Mythic+ score prefers `raiderIo.currentSeasonScore`.

This is a frontend-only fix using known raid names. It does not fetch full historical progression from external APIs.
