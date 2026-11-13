# DRAEKHORR Forever V2.9.5

Combines the V2.9.4 Full Throttle hero copy with the V2.9.5 artwork edge fade.

## Upload only these files

- `forever/index.html` — V2.9.4 hero text, stylesheet cache version 2.9.5.
- `forever/style.css` — existing V2.7 layout rules plus a mask on `.hero-art` to blend its edges.

The hero image is not modified or regenerated. Keep `forever/assets/avatar.png`, `forever/script.js`, `forever/data.json`, all backend scripts, and workflows as they are.

Commit to GitHub, wait for Pages deployment, then hard refresh. No API sync required.

Note: The mask fades the outer edges of the artwork, which may also slightly soften decorative details near the border.
