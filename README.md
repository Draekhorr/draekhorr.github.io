# DRAEKHORR Forever V2.9.3 — Talent parsing

Replace `scripts/sync_forever.py`, then run **Sync WoW Forever**. This update reads two or three named Shaman talent trees. It assigns zero to an absent tree only if the other trees account for all classic talent points at the verified character level (level minus 9). Otherwise it preserves the last-known-good value and emits diagnostic lines. Professions and item level are unchanged. No frontend changes.
