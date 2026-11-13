# DRAEKHORR V2.5 — Forever profile sync

This is an **incremental update**, not a complete replacement of the website. Keep all Retail files and existing workflows unchanged.

## Install

Copy `scripts/sync_forever.py`, `forever/script.js`, and `forever/index.html` to the same repository paths. Add `.github/workflows/sync-forever.yml` manually using GitHub's **Create new file** if the hidden `.github` directory is skipped by upload. Keep `forever/style.css` and `forever/assets/avatar.png` from V2.4.

Commit to `main`, then run **Actions → Sync WoW Forever → Run workflow**. After the workflow commits `forever/data.json`, refresh `/forever/`.

## Data contract

`forever/data.json` is generated from the public `https://forever.raider.io/api/v1/characters/profile` endpoint. The script attempts `region=eu`, `realm=normal`, `name=Draekhorr Healstappen`, with a `ruleset=normal` fallback. It accepts only a profile matching the requested full name. It never scrapes HTML or copies Retail stats. Missing API fields stay blank; existing verified values are retained.

**Important:** The Forever Raider.IO API is published, but its exact query parameters and response fields for this character have not been tested from this environment. If both requests fail, the workflow fails without overwriting existing data. Check `DIAG FOREVER` output to identify the actual API response. `profileUrl` is the permanent public attribution link.

The workflow runs every six hours at minute 25 to reduce collisions with the Retail sync, but concurrent Git pushes can still conflict. It uses rebase, never force push.
