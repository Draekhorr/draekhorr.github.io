# DRAEKHORR Forever V2.8 — Blizzard profile enrichment

Adds optional Blizzard Forever API enrichment to the existing independent Forever page. Keeps the existing V2.7 layout and Raider.IO character data. No changes to Retail.

## Install

Upload `scripts/sync_forever.py` and `forever/script.js`. Manually update `.github/workflows/sync-forever.yml` (GitHub web upload may omit hidden directories). Keep `forever/index.html` and `forever/style.css` unchanged.

The workflow passes the existing `BLIZZARD_CLIENT_ID` and `BLIZZARD_CLIENT_SECRET` GitHub Secrets to the script. Do not commit credentials. Run **Sync WoW Forever** manually once and inspect `DIAG FOREVER Blizzard profile status=...` and `OK FOREVER profile saved fields=...`.

The experimental Blizzard namespace is `profile-forever-eu` and character slug `draekhorr-healstappen` (no realm). Character API: `GET https://eu.api.blizzard.com/profile/wow/character/draekhorr-healstappen?namespace=profile-forever-eu`. `average_item_level` and `equipped_item_level` are read from the profile when present. The script also queries `/specializations`, but deliberately does not guess a 9/7/0 build: talent totals appear only if three explicit `spent_points` values are returned. Otherwise `—` remains.

Blizzard Forever API support is not yet officially documented and can change. Missing or failed API responses preserve the last known verified values. No HTML scraping or fabricated values. The actual API response has **not** been tested with your secrets.
