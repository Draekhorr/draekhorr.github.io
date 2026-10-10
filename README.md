# Draekhorr — Azeroth Legacy (V3)

Static World of Warcraft character showcase for Draekhorr, EU-Draenor.

## Changes in V3
- Raid Progression is the first content section after the hero.
- Raider.IO is second, with fields for current score, previous season, ranking and best runs.
- Cutting Edge history and WoWProgress follow.
- Mounts and Achievements are side-by-side 50/50 on desktop and stacked on mobile.
- Uses the supplied Draekhorr avatar.

## Publish
Upload the **contents** of this folder (not the folder itself) to the root of the `Draekhorr/draekhorr.github.io` repository, replacing the existing files. Commit to `main`. GitHub Pages will deploy the new version.

## Data
`data.json` contains placeholders. `script.js` displays real data only when added to the JSON. This release **does not** connect to Blizzard, Raider.IO or WoWProgress APIs automatically. GitHub Actions and an API sync script must be added separately. Do not put Blizzard client secrets in any public file.

`accountWideMountCount` should only be filled using a verified account-wide source. The old `mountCount` is supported as a fallback for compatibility, but must not be mislabeled account-wide unless verified.

`cuttingEdgeAchievements` entries require `verified: true`; unique `tierId` values determine the Cutting Edge raid tier count.
