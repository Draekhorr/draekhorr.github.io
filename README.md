# DRAEKHORR Forever V2.9.10 — Dominant Talent Specialization

Small update based on the working V2.9.9 talent parser.

- `scripts/sync_forever.py`: derives `role` from the largest verified Elemental / Enhancement / Restoration talent allocation. Tied highest allocations are labeled `Hybrid`. All-zero or unverified builds are not classified. Existing verified talent parsing and professions remain unchanged.
- `forever/script.js`: displays the derived specialization before class/race (for example `Enhancement Shaman · Dwarf`). When classification is unavailable, retains `Shaman · Dwarf`.
- No changes to Retail, API credentials, GitHub Actions, CSS, artwork, or HTML.

## Install

Replace the two files at their respective paths. Commit, then run **Actions → Sync WoW Forever → Run workflow** once to populate the new `role` field. Scheduled runs continue as before. After Pages deployment, refresh the Forever page.

The script only classifies a build when the Blizzard talent parser returns a verified allocation; the public API is experimental. This update does not change the schedule itself.
