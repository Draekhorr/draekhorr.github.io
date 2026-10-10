#!/usr/bin/env python3

import os
import json
import re
import sys
import base64
import datetime
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data.json"

REGION = "eu"
REALM = "draenor"
NAME = "draekhorr"

CURRENT_SEASON = "season-mn-2"
PREVIOUS_SEASON = "season-mn-1"

PROFILE_URL = (
    "https://raider.io/characters/eu/draenor/"
    "Draekhorr?season=season-mn-2"
)

WCL_URL = (
    "https://www.warcraftlogs.com/character/"
    "eu/draenor/draekhorr"
)

HEADERS = {
    "User-Agent": "DraekhorrWoWLegacy/4.0"
}


def request(url, headers=None, body=None):

    h = {**HEADERS, **(headers or {})}

    if isinstance(body, dict):
        body = urllib.parse.urlencode(body).encode()
        h.setdefault(
            "Content-Type",
            "application/x-www-form-urlencoded"
        )

    req = urllib.request.Request(
        url,
        data=body,
        headers=h
    )

    with urllib.request.urlopen(
        req,
        timeout=30
    ) as response:
        return json.load(response)


def token(url, cid, secret):

    auth = base64.b64encode(
        f"{cid}:{secret}".encode()
    ).decode()

    result = request(
        url,
        {"Authorization": "Basic " + auth},
        {"grant_type": "client_credentials"}
    )

    return result["access_token"]


def update(section, function, data):

    try:
        result = function()

        if result is None:
            return False

        if section is None:
            data.update(result)
        else:
            previous = data.get(section) or {}
            data[section] = {
                **previous,
                **result
            }

        print(f"OK {section or function.__name__}")
        return True

    except Exception as exc:

        print(
            f"WARN {section or function.__name__}: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr
        )

        return False


# ==========================================
# RAIDER.IO
# ==========================================

RAID_METADATA = {

    "the-venomous-abyss": {
        "name": "The Venomous Abyss",
        "expansion": "Midnight",
        "season": CURRENT_SEASON
    },

    "the-tidebound-grotto": {
        "name": "The Tidebound Grotto",
        "expansion": "Midnight",
        "season": CURRENT_SEASON
    },

    "sporefall": {
        "name": "Sporefall",
        "expansion": "Midnight",
        "season": PREVIOUS_SEASON
    },

    "tier-mn-1": {
        "name": "Midnight Season 1 Raid",
        "expansion": "Midnight",
        "season": PREVIOUS_SEASON
    }

}


def rio():

    fields = (
        "mythic_plus_scores_by_season:"
        f"{CURRENT_SEASON},"
        "mythic_plus_scores_by_season:"
        f"{PREVIOUS_SEASON},"
        "mythic_plus_best_runs,"
        "raid_progression"
    )

    params = urllib.parse.urlencode({
        "region": REGION,
        "realm": REALM,
        "name": NAME,
        "fields": fields
    })

    obj = request(
        "https://raider.io/api/v1/"
        "characters/profile?" + params
    )

    seasons = obj.get(
        "mythic_plus_scores_by_season"
    ) or []

    def get_score(season):

        for entry in seasons:

            if entry.get("season") == season:
                return (
                    entry.get("scores") or {}
                ).get("all")

        return None

    current_score = get_score(CURRENT_SEASON)
    previous_score = get_score(PREVIOUS_SEASON)

    if current_score is None:
        raise ValueError(
            "Current season score unavailable"
        )

    runs = []

    for run in obj.get(
        "mythic_plus_best_runs"
    ) or []:

        url = run.get("url") or ""

        if f"/{CURRENT_SEASON}/" not in url:
            continue

        runs.append({
            "name": (
                f"{run.get('dungeon', 'Dungeon')} "
                f"+{run.get('mythic_level', '?')}"
            ),
            "note": (
                f"Score: {run.get('score', 'N/A')}"
            ),
            "url": url
        })

    current_raids = []
    previous_raids = []
    unknown_raids = []

    for slug, progress in (
        obj.get("raid_progression") or {}
    ).items():

        if not isinstance(progress, dict):
            continue

        normalized = re.sub(
            r"[^a-z0-9]+",
            "-",
            slug.lower()
        ).strip("-")

        meta = RAID_METADATA.get(normalized)

        entry = {
            "name": (
                meta["name"]
                if meta
                else slug.replace("-", " ").title()
            ),
            "note": progress.get("summary") or "",
            "url": PROFILE_URL,
            "sourceSlug": slug,
            "source": "Raider.IO"
        }

        if not meta:
            unknown_raids.append(entry)

        elif meta["season"] == CURRENT_SEASON:
            current_raids.append(entry)

        elif meta["season"] == PREVIOUS_SEASON:
            previous_raids.append(entry)

    history = {
        "Midnight": [
            {
                "season": PREVIOUS_SEASON,
                "seasonName": "Midnight Season 1",
                "raids": previous_raids
            }
        ]
    }

    result = {

        "raiderIo": {
            "currentSeason": CURRENT_SEASON,
            "currentSeasonName": "Midnight Season 2",
            "currentSeasonScore": current_score,
            "mythicPlusScore": current_score,
            "previousSeason": PREVIOUS_SEASON,
            "previousSeasonScore": previous_score,
            "bestRuns": runs,
            "profileUrl": PROFILE_URL
        },

        "raidProgression": current_raids,

        "raidProgressionByExpansion": {
            "currentSeason": {
                "expansion": "Midnight",
                "season": CURRENT_SEASON,
                "seasonName": "Midnight Season 2",
                "raids": current_raids
            },
            "history": history
        },

        "unclassifiedRaidProgression": unknown_raids,

        "raidSourceUrl": PROFILE_URL
    }

    return result


# ==========================================
# BLIZZARD API
# ==========================================

EXPANSION_RAIDS = {

    "Legion": [
        "The Emerald Nightmare",
        "Trial of Valor",
        "The Nighthold",
        "Tomb of Sargeras",
        "Antorus, the Burning Throne"
    ],

    "Battle for Azeroth": [
        "Uldir",
        "Battle of Dazar'alor",
        "Crucible of Storms",
        "The Eternal Palace",
        "Ny'alotha, the Waking City"
    ],

    "Shadowlands": [
        "Castle Nathria",
        "Sanctum of Domination",
        "Sepulcher of the First Ones"
    ],

    "Dragonflight": [
        "Vault of the Incarnates",
        "Aberrus, the Shadowed Crucible",
        "Amirdrassil, the Dream's Hope"
    ],

    "The War Within": [
        "Nerub-ar Palace",
        "Liberation of Undermine",
        "Manaforge Omega"
    ]

}


def find_expansion(raid_name):

    name = raid_name.casefold()

    for expansion, raids in EXPANSION_RAIDS.items():

        for raid in raids:

            if raid.casefold() == name:
                return expansion

    return None


def parse_historical_raids(encounters):

    history = {}

    raids = encounters.get("expansions") or []

    for expansion_data in raids:

        expansion_name = (
            (expansion_data.get("expansion") or {}).get("name")
            or "Unknown Expansion"
        )

        for raid in expansion_data.get("instances") or []:

            instance = raid.get("instance") or {}

            raid_name = instance.get("name")

            if not raid_name:
                continue

            known_expansion = find_expansion(raid_name)

            if known_expansion:
                expansion_name = known_expansion

            modes = raid.get("modes") or []

            mythic_bosses = set()
            mythic_encounters = []

            for mode in modes:

                difficulty = mode.get("difficulty") or {}

                difficulty_name = (
                    difficulty.get("name") or ""
                ).lower()

                if difficulty_name != "mythic":
                    continue

                for encounter in mode.get("progress") or []:

                    encounter_data = (
                        encounter.get("encounter") or {}
                    )

                    encounter_id = encounter_data.get("id")
                    encounter_name = encounter_data.get("name")

                    if encounter_id is None:
                        continue

                    completed = encounter.get("completed_count")

                    if completed is None:
                        completed = encounter.get("completed")

                    if isinstance(completed, bool):
                        killed = completed
                    elif isinstance(completed, (int, float)):
                        killed = completed > 0
                    else:
                        killed = False

                    if killed:
                        mythic_bosses.add(encounter_id)

                    mythic_encounters.append({
                        "id": encounter_id,
                        "name": encounter_name,
                        "completed": killed
                    })

            if not mythic_encounters:
                continue

            entry = {
                "name": raid_name,
                "mythicKills": len(mythic_bosses),
                "totalBosses": None,
                "note": (
                    f"{len(mythic_bosses)} confirmed "
                    "Mythic encounter kills"
                ),
                "source": "Blizzard",
                "bosses": mythic_encounters
            }

            history.setdefault(
                expansion_name,
                []
            ).append(entry)

    return history


def blizzard():

    cid = os.getenv("BLIZZARD_CLIENT_ID")
    secret = os.getenv("BLIZZARD_CLIENT_SECRET")

    if not cid or not secret:
        raise RuntimeError(
            "Missing Blizzard credentials"
        )

    access = token(
        "https://oauth.battle.net/token",
        cid,
        secret
    )

    headers = {
        "Authorization": "Bearer " + access
    }

    def get(path):

        separator = "&" if "?" in path else "?"

        return request(
            "https://eu.api.blizzard.com"
            + path
            + separator
            + "namespace=profile-eu&locale=en_GB",
            headers
        )

    changes = {}

    base = (
        f"/profile/wow/character/{REALM}/{NAME}"
    )

    # Character profile

    profile = get(base)

    changes["character"] = {
        "name": profile.get("name"),
        "level": profile.get("level"),
        "class": (
            profile.get("character_class") or {}
        ).get("name"),
        "race": (
            profile.get("race") or {}
        ).get("name"),
        "itemLevel": profile.get(
            "equipped_item_level"
        )
    }

    changes["achievementPoints"] = (
        profile.get("achievement_points")
    )

    # Cutting Edge achievements

    try:

        achievements = get(
            base + "/achievements"
        )

        cutting_edge = []

        for item in achievements.get(
            "achievements"
        ) or []:

            achievement = item.get(
                "achievement"
            ) or {}

            title = achievement.get("name") or ""

            if not re.search(
                r"^Cutting Edge:",
                title,
                re.IGNORECASE
            ):
                continue

            achievement_id = achievement.get("id")

            timestamp = item.get(
                "completed_timestamp"
            )

            cutting_edge.append({
                "name": title,
                "tierId": str(achievement_id),
                "verified": timestamp is not None,
                "note": str(timestamp or ""),
                "url": (
                    "https://www.wowhead.com/"
                    f"achievement={achievement_id}"
                )
            })

        changes["cuttingEdgeAchievements"] = (
            cutting_edge
        )

    except Exception as exc:

        print(
            "WARN Blizzard achievements:",
            exc,
            file=sys.stderr
        )

    # Mount collection

    try:

        mounts = get(
            base + "/collections/mounts"
        )

        entries = mounts.get("mounts") or []

        changes["characterMountCount"] = (
            len(entries)
        )

    except Exception as exc:

        print(
            "WARN Blizzard mounts:",
            exc,
            file=sys.stderr
        )

    # Historical raid encounters

    try:

        encounters = get(
            base + "/encounters/raids"
        )

        historical = parse_historical_raids(
            encounters
        )

        if historical:
            changes["historicalRaidProgression"] = (
                historical
            )

            print(
                "Historical raid expansions:",
                list(historical.keys())
            )

        else:
            print(
                "WARN No confirmed historical "
                "Mythic encounters found"
            )

    except Exception as exc:

        print(
            "WARN Blizzard historical raids:",
            exc,
            file=sys.stderr
        )

    return changes


# ==========================================
# WARCRAFT LOGS
# ==========================================

def warcraftlogs():

    cid = os.getenv(
        "WARCRAFTLOGS_CLIENT_ID"
    )

    secret = os.getenv(
        "WARCRAFTLOGS_CLIENT_SECRET"
    )

    if not cid or not secret:
        raise RuntimeError(
            "Missing Warcraft Logs credentials"
        )

    access = token(
        "https://www.warcraftlogs.com/oauth/token",
        cid,
        secret
    )

    query = """
    query(
      $name: String!,
      $server: String!,
      $region: String!
    ) {
      characterData {
        character(
          name: $name,
          serverSlug: $server,
          serverRegion: $region
        ) {
          id
          name
          zoneRankings
        }
      }
    }
    """

    body = json.dumps({
        "query": query,
        "variables": {
            "name": "Draekhorr",
            "server": REALM,
            "region": "EU"
        }
    }).encode()

    req = urllib.request.Request(
        "https://www.warcraftlogs.com/api/v2/client",
        data=body,
        headers={
            **HEADERS,
            "Authorization": "Bearer " + access,
            "Content-Type": "application/json"
        }
    )

    with urllib.request.urlopen(
        req,
        timeout=30
    ) as response:
        result = json.load(response)

    if result.get("errors"):
        raise RuntimeError(
            str(result["errors"])[:500]
        )

    character = (
        ((result.get("data") or {})
         .get("characterData") or {})
        .get("character")
    )

    if not character:
        raise RuntimeError(
            "Character not found in Warcraft Logs"
        )

    ranking = character.get(
        "zoneRankings"
    ) or {}

    if not isinstance(ranking, dict):
        ranking = {}

    boss_parses = []

    for row in ranking.get(
        "rankings"
    ) or []:

        if not isinstance(row, dict):
            continue

        percentile = row.get("rankPercent")

        if percentile is None:
            continue

        encounter = row.get("encounter") or {}

        boss_name = (
            encounter.get("name", "Boss")
            if isinstance(encounter, dict)
            else "Boss"
        )

        boss_parses.append({
            "name": boss_name,
            "note": (
                f"Rank percentile: {percentile}"
            ),
            "url": WCL_URL
        })

    return {
        "profileUrl": WCL_URL,
        "bestPerformanceAverage": ranking.get(
            "bestPerformanceAverage"
        ),
        "medianPerformanceAverage": ranking.get(
            "medianPerformanceAverage"
        ),
        "bossParses": boss_parses
    }


# ==========================================
# MAIN SYNC
# ==========================================

def main():

    if OUT.exists():
        data = json.loads(
            OUT.read_text(encoding="utf-8")
        )
    else:
        data = {}

    results = []

    results.append(
        update(None, rio, data)
    )

    results.append(
        update("warcraftLogs", warcraftlogs, data)
    )

    results.append(
        update(None, blizzard, data)
    )

    if not any(results):

        print(
            "ERROR: All API integrations failed",
            file=sys.stderr
        )

        sys.exit(1)

    # Merge historical Blizzard raids into
    # the expansion-based structure.

    historical = data.get(
        "historicalRaidProgression"
    ) or {}

    progression = data.get(
        "raidProgressionByExpansion"
    ) or {}

    history = progression.get("history") or {}

    for expansion, raids in historical.items():

        if expansion == "Midnight":
            continue

        existing = history.get(expansion) or []

        # Preserve existing season-grouped history.
        if not existing:
            history[expansion] = [
                {
                    "season": None,
                    "seasonName": "Historical Raids",
                    "raids": raids
                }
            ]

    progression["history"] = history

    data["raidProgressionByExpansion"] = (
        progression
    )

    data["updatedAt"] = (
        datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(timespec="seconds")
    )

    OUT.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8"
    )

    print("Wrote data.json")


if __name__ == "__main__":
    main()
