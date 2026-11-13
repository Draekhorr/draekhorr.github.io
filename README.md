# DRAEKHORR V2.4 — Forever page (additive update)

This is an **additive** package, not a full replacement of the existing V2 website.

## Upload

- **Replace** `components/header.html` in the existing repository (adds `FOREVER ↗` to the existing navigation).
- **Add** `assets/css/forever-nav.css`.
- **Add** the entire `forever/` directory (`index.html`, `style.css`, `script.js`, `assets/avatar.png`).
- In the existing root `index.html`, add `<link rel="stylesheet" href="assets/css/forever-nav.css?v=2.4">` inside `<head>`, after the existing CSS links. **Do not replace the root index.html**: this preserves the current Cloudflare Analytics beacon and other site settings.

## Data and artwork

- Forever profile: https://forever.raider.io/characters/eu/normal/Draekhorr%20Healstappen
- This starter page intentionally does **not** invent character level, race, guild, or statistics. An optional `forever/data.json` can supply verified `name`, `role`, `level`, `class`, `race`, `guild` fields later.
- The hero artwork is the existing DRAEKHORR asset reused as a temporary visual. Replace `forever/assets/avatar.png` when Forever-specific artwork is available.
- Retail APIs, data.json, GitHub Actions, and Cloudflare analytics are unchanged. No workflow run is required for this page.

## Verification

After GitHub Pages deploy, visit `/forever/`, click `RETAIL`, and check the existing header's `FOREVER` link. Test at mobile width. The package was checked structurally; it was not browser-tested against the live repository.
