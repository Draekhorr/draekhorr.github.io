Draekhorr V4.6 frontend + WCL sync

Upload index.html, script.js, style.css to repository root and scripts/sync_all.py to scripts/. Do not replace data.json or secrets.

Raid History now uses one expansion selector, initially closed. Warcraft Logs renders real boss icons ONLY when iconUrl is available in data.json. The current Warcraft Logs ranking API response may not provide icon URLs; missing icons remain absent (no generated or invented images). The backend preserves existing valid iconUrl values and reads them if included in encounter metadata. To populate missing icons, a verified encounter-to-image source is still needed.

Run Sync WoW APIs after upload, then refresh Pages.
