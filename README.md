# Draekhorr WoW Legacy — V4

Static GitHub Pages website for Draekhorr (EU-Draenor).

## V4 changes
- Mythic Raid Progression and Warcraft Logs share one section, in two equal columns on desktop and stacked on mobile.
- Raider.IO follows directly after the combined raid section.
- Cutting Edge Legacy, WoWProgress, then Mounts and Achievements (two columns).
- Original Draekhorr artwork retained.

## Publish
Upload the **contents** of this ZIP to the root of `Draekhorr/draekhorr.github.io` and commit changes. Keep GitHub Pages configured for `main` / `(root)`.

## Data and security
This is a frontend/layout update, **not yet a live API integration**. No scores, raid kills, or parses are fabricated. `data.json` contains null values until verified data is fetched.

To populate the combined section, write `raidProgression` as an array of `{ "name": "...", "note": "...", "url": "https://..." }` and `warcraftLogs` as `{ "bestPerformanceAverage": number|null, "medianPerformanceAverage": number|null, "bossParses": [{"name":"...","note":"...","url":"https://..."}], "profileUrl":"https://..." }`. The other fields follow the V3 schema.

Never put Blizzard or Warcraft Logs client secrets into the repository, `data.json`, or browser JavaScript. Future API sync should run server-side (e.g. GitHub Actions) and commit only public results.

The `accountWideMountCount` field must only be populated from a verified account-wide source, not from character-only mount counts.
