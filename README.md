# DRAEKHORR Forever V2.9.2 — Talents diagnostics and parsing

This is a focused update to `scripts/sync_forever.py` based on the working V2.9.1 file.

- Preserves profession parsing, item level, portrait, and other fields.
- Examines Blizzard `specialization_groups` and recognizes explicitly named Elemental, Enhancement, and Restoration trees.
- Reads explicit spent-point totals, or sums individually reported talent ranks only if complete.
- Selects a uniquely active group (or the sole available group). Ambiguous or incomplete data remains unavailable; last-known-good values are preserved.
- Prints structural diagnostics without dumping full character responses.

## Install
Replace `scripts/sync_forever.py`, commit, and manually run **Sync WoW Forever**. No frontend or workflow changes required.

## Verify
Look for `DIAG FOREVER talents group[...]`, `DIAG FOREVER talents ...`, and ideally `OK FOREVER verified talents=...`. The actual Blizzard Forever specialization response structure has not been verified here. If there is no `OK`, share those diagnostic lines; further mapping may be needed.
