Draekhorr V4.9.2 frontend hotfix

Upload index.html and script.js to repository root. Do not replace style.css, data.json, scripts/sync_all.py, or GitHub Actions workflow.

Changes: versioned JS and JSON fetch to avoid stale caches; bestPercent shown with one decimal and %; highestHps displayed as rounded integer, with zero/null as dash.

IMPORTANT: index.html is based on the previously provided V4.8 markup. If you have customized index.html since then, upload ONLY script.js and change the existing script tag to src="script.js?v=4.9.2" manually.

No API sync is required; wait for Pages deployment and hard refresh. Boss images still require iconUrl from backend.
