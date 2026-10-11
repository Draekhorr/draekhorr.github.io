# DRAEKHORR V2 — Modular Frontend

Static World of Warcraft character portfolio deployed on GitHub Pages. V2 is a **structural refactor** of the V1.5.7 frontend, with the Raider.IO historical backfill script from V1.5.8 included. It intentionally preserves the existing appearance and behavior.

## Project layout

- `index.html`: lightweight shell and component mount points.
- `components/*.html`: independently editable header, hero, character, raids, Mythic+, outro and footer sections.
- `js/main.js`: loads all HTML components, then fetches `data.json` and renders sections.
- `js/{header,character,raids,warcraftlogs,mythicplus}.js`: ES modules for each feature.
- `js/utils.js`: shared DOM helpers.
- `assets/css/base.css`: unchanged V1 styles, moved from `style.css`.
- `assets/css/components.css`: place new component-specific rules here; imported by `index.html`.
- `scripts/`: existing API sync/backfill scripts (not refactored in this release).
- `data.json`: **remains at repository root** and is maintained by the existing GitHub Actions workflows.

## Deploy

1. Upload `index.html`, `components/`, `js/`, `assets/` and the included `scripts/` files **without deleting** existing root `data.json`, images, or workflows.
2. Keep existing `avatar.png` at repository root (the HTML references it). If not already in your repository, restore it from your previous deployment.
3. Keep existing `.github/workflows/sync.yml`, `wcl-backfill.yml`, guild sync and monitoring workflows. `rio-backfill.yml` is included for manual installation if not already present.
4. Commit to your GitHub Pages publishing branch and verify deployment.

**Important:** Run through GitHub Pages or `python -m http.server 8000` from the project root. Opening `index.html` using `file://` will fail because ES modules and HTML components require HTTP.

## Editing

- Header / guild → `components/header.html` and `js/header.js`.
- Character profile → `components/character.html` and `js/character.js`.
- Raid history → `components/raids.html` and `js/raids.js`.
- Raid Warcraft Logs → `components/raids.html` and `js/warcraftlogs.js`.
- Mythic+ → `components/mythicplus.html` and `js/mythicplus.js`.
- Visual changes → `assets/css/components.css` first; shared V1 rules are in `assets/css/base.css`.

## Data & automation

No API secrets are embedded in the frontend. Existing GitHub Actions can continue to update root `data.json` every six hours. Raid Warcraft Logs are kept separate from Raider.IO Mythic+; no M+ Warcraft Logs are shown. Historical M+ dungeon cards require verified season-specific Raider.IO data.

## Verification

Syntax check: `node --check js/*.js` (check each file individually if your Node version does not accept globs). Test on desktop, ultrawide and mobile after deployment. A live browser regression test against production data has **not** been performed in this package.
