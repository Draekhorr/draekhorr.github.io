# Draekhorr V4.9.5 — Boss icons

Replace ONLY `scripts/sync_all.py` in the repository. Do not replace `data.json`, `script.js`, GitHub Actions workflow, or secrets.

Then run Actions > Sync WoW APIs > Run workflow. After the workflow commits the updated data.json and Pages deploys, refresh the website.

Boss image URLs are constructed from Warcraft Logs encounter IDs using the RPGLogs CDN pattern supplied by the site owner. Availability is not verified for every encounter. The existing frontend handles broken image links with a placeholder. The `icons=` log count indicates URLs populated, not successful image downloads.
