# Draekhorr WoW showcase

This is a ready-to-publish static website for Draekhorr on EU Draenor. Statistics are intentionally blank until verified; no rare mount ownership has been assumed.

## Publish with GitHub Pages
1. Create a free account at https://github.com/signup
2. Create a public repository named `YOURUSERNAME.github.io`.
3. Upload `index.html`, `style.css`, `script.js`, `data.json` into the repository root.
4. Go to Settings > Pages, choose Deploy from a branch, main, / (root).
5. Open `https://YOURUSERNAME.github.io` after deployment.

## Collection data
Edit `data.json` with your verified `mountCount`, `achievementPoints`, and arrays of mounts/achievements. Mount entries look like `{"name":"Mount name","rare":true,"note":"Where it came from"}`; achievements look like `{"name":"Achievement name","note":"Feats of Strength"}`. Add `updatedAt` when refreshed.

Blizzard's profile APIs can provide character, mounts, and achievements with a server-side OAuth client credentials token. Never place a Blizzard API client secret in this public repository or browser JavaScript. A future GitHub Actions sync can store credentials in repository secrets. Rarity percentages require independent verified data.

## Raider.IO, WoWProgress and Cutting Edge
The site now includes a raid progression section, Raider.IO character link, WoWProgress link, and a Cutting Edge history panel. These are **not yet automatically synced**. Unknown stats display a dash rather than fabricated results.

For verified data, populate `data.json`:
- `raiderIo.mythicPlusScore`: numeric score from Raider.IO; its public character API can be queried by a future sync job.
- `raiderIo.profileUrl`: direct character profile URL.
- `wowprogress.profileUrl`: verified WoWProgress character URL. Until then, the button opens the service homepage; WowProgress data may require manual updates if there is no supported public API.
- `raidProgression`: list of `{ "name": "Raid name", "note": "Verified Mythic progress" }`.
- `cuttingEdgeAchievements`: list of `{ "name": "Cutting Edge: Boss", "tierId": "unique-tier-key", "note": "Raid / expansion", "verified": true }` sourced from verified Blizzard achievement completions. `tierId` must be the same for achievements belonging to the same tier. The site computes both total verified CE achievements and the number of unique raid tiers with CE.

Do not set `verified: true` without checking character/account achievement data and timestamps. Some historical achievements may be account-wide; label their scope accurately. The `avatar.png` is the provided Draekhorr artwork.
