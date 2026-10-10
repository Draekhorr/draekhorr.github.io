# Draekhorr V4.3 - combined frontend + sync

Upload the CONTENTS of this package to the root of Draekhorr/draekhorr.github.io (main branch), preserving the `scripts/` folder.

Replace these files:
- index.html
- style.css
- script.js
- scripts/sync_all.py

Do NOT replace data.json, avatar.png, .github/workflows/sync.yml or any GitHub secrets.

Then run Actions > Sync WoW APIs > Run workflow, and wait for the Pages deployment. Hard refresh the site.

Frontend reads `raidProgressionByExpansion.history` and `historicalRaidProgression`, falling back to known Midnight raid mapping when history is missing. Historical Mythic/Heroic entries only, with expansion dropdowns. Warcraft Logs stays next to raid progression.

IMPORTANT: The bundled Python sync is the previously provided V4.2 and has not been verified against the live Blizzard API. If the historical parser returns no data, the website will show the known Midnight raids only. The Blizzard API may not supply complete historical records. Do not interpret absent raids as zero kills.
