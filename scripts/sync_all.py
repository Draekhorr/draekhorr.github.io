#!/usr/bin/env python3
"""Draekhorr WoW Legacy sync. Secrets are read only from environment."""
import base64
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data.json'
REGION, REALM, NAME = 'eu', 'draenor', 'draekhorr'
CURRENT, PREVIOUS = 'season-mn-2', 'season-mn-1'
RIO_URL = f'https://raider.io/characters/{REGION}/{REALM}/Draekhorr?season={CURRENT}'
WCL_URL = f'https://www.warcraftlogs.com/character/{REGION}/{REALM}/{NAME}'
USER_AGENT = 'DraekhorrWoWLegacy/4.2'

# These are known season associations, not inferred from raid order.
RAID_SEASONS = {
    'the-venomous-abyss': (CURRENT, 'The Venomous Abyss'),
    'the-tidebound-grotto': (CURRENT, 'The Tidebound Grotto'),
    'sporefall': (PREVIOUS, 'Sporefall'),
    'tier-mn-1': (PREVIOUS, 'Tier MN 1 (unresolved raid label)'),
}


def http_json(url, headers=None, form=None, json_body=None):
    hdr = {'User-Agent': USER_AGENT, **(headers or {})}
    body = None
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        hdr['Content-Type'] = 'application/x-www-form-urlencoded'
    if json_body is not None:
        body = json.dumps(json_body).encode()
        hdr['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=body, headers=hdr)
    with urllib.request.urlopen(req, timeout=35) as resp:
        return json.load(resp)


def oauth(url, id_name, secret_name):
    cid, secret = os.getenv(id_name), os.getenv(secret_name)
    if not cid or not secret:
        raise RuntimeError('Missing credentials for ' + id_name)
    basic = base64.b64encode(f'{cid}:{secret}'.encode()).decode()
    return http_json(url, {'Authorization': 'Basic ' + basic},
                     form={'grant_type': 'client_credentials'})['access_token']


def as_dict(value):
    return value if isinstance(value, dict) else {}


def as_list(value):
    return value if isinstance(value, list) else []


def normalize(value):
    return re.sub(r'[^a-z0-9]+', '-', str(value).lower()).strip('-')


def score_for(payload, season):
    for row in as_list(payload.get('mythic_plus_scores_by_season')):
        if as_dict(row).get('season') == season:
            val = as_dict(row.get('scores')).get('all')
            if isinstance(val, (float, int)):
                return val
    return None


def sync_rio(data):
    fields = ','.join([
        f'mythic_plus_scores_by_season:{CURRENT}',
        f'mythic_plus_scores_by_season:{PREVIOUS}',
        'mythic_plus_best_runs', 'raid_progression'
    ])
    url = 'https://raider.io/api/v1/characters/profile?' + urllib.parse.urlencode({
        'region': REGION, 'realm': REALM, 'name': NAME, 'fields': fields
    })
    payload = http_json(url)
    rio = dict(as_dict(data.get('raiderIo')))
    current_score = score_for(payload, CURRENT)
    previous_score = score_for(payload, PREVIOUS)
    rio.update({'currentSeason': CURRENT, 'currentSeasonName': 'Midnight Season 2',
                'previousSeason': PREVIOUS, 'previousSeasonName': 'Midnight Season 1',
                'profileUrl': RIO_URL})
    if current_score is not None:
        rio['currentSeasonScore'] = current_score
        rio['mythicPlusScore'] = current_score
    else:
        print('WARN RIO current score not supplied; preserving last known value')
    if previous_score is not None:
        rio['previousSeasonScore'] = previous_score
    valid_scores = [s for s in (current_score, previous_score, rio.get('bestHistoricalScore'))
                    if isinstance(s, (int, float))]
    if valid_scores:
        rio['bestHistoricalScore'] = max(valid_scores)
    if isinstance(payload.get('mythic_plus_best_runs'), list):
        runs = []
        for run in payload['mythic_plus_best_runs']:
            run = as_dict(run)
            link = run.get('url') or ''
            if f'/{CURRENT}/' not in link:
                continue
            runs.append({'name': f"{run.get('dungeon', 'Dungeon')} +{run.get('mythic_level', '?')}",
                         'note': f"Score: {run.get('score', 'N/A')} | Timed: {run.get('is_completed_within_time', 'N/A')}",
                         'url': link})
        rio['bestRuns'] = runs
    data['raiderIo'] = rio
    raw = as_dict(payload.get('raid_progression'))
    current_raids, previous_raids, unknown = [], [], []
    for slug, progress in raw.items():
        progress = as_dict(progress)
        key = normalize(slug)
        season, name = RAID_SEASONS.get(key, (None, str(slug).replace('-', ' ').title()))
        entry = {'name': name, 'note': progress.get('summary') or '',
                 'url': RIO_URL, 'source': 'Raider.IO', 'sourceSlug': slug}
        if season == CURRENT:
            current_raids.append(entry)
        elif season == PREVIOUS:
            previous_raids.append(entry)
        else:
            unknown.append(entry)
    if raw:
        data['raidProgression'] = current_raids
        data['unclassifiedRaidProgression'] = unknown
    # Always write the season grouping even if the API's raid data is absent.
    progression = dict(as_dict(data.get('raidProgressionByExpansion')))
    progression['currentSeason'] = {'expansion': 'Midnight', 'season': CURRENT,
                                    'seasonName': 'Midnight Season 2',
                                    'raids': current_raids if raw else as_list(data.get('raidProgression'))}
    history = dict(as_dict(progression.get('history')))
    history['Midnight'] = [{'season': PREVIOUS, 'seasonName': 'Midnight Season 1',
                            'raids': previous_raids}]
    progression['history'] = history
    data['raidProgressionByExpansion'] = progression
    data['raidSourceUrl'] = RIO_URL
    print(f'OK raiderio; current score={current_score}; previous score={previous_score}; current raids={len(current_raids)}')


def select_difficulty(modes):
    """Prefer Mythic if present, otherwise Heroic. Never fall back to Heroic if Mythic exists."""
    available = {}
    for mode in as_list(modes):
        mode = as_dict(mode)
        difficulty = as_dict(mode.get('difficulty'))
        kind = str(difficulty.get('type') or difficulty.get('name') or '').upper()
        if 'MYTHIC' in kind:
            available['MYTHIC'] = mode
        elif 'HEROIC' in kind:
            available['HEROIC'] = mode
    if 'MYTHIC' in available:
        return 'MYTHIC', available['MYTHIC']
    if 'HEROIC' in available:
        return 'HEROIC', available['HEROIC']
    return None, None


def parse_encounters(payload):
    """Blizzard: expansions[].instances[].modes[].progress is an object."""
    result = {}
    for expansion in as_list(as_dict(payload).get('expansions')):
        expansion = as_dict(expansion)
        exp_name = as_dict(expansion.get('expansion')).get('name')
        if not exp_name:
            continue
        for raid in as_list(expansion.get('instances')):
            raid = as_dict(raid)
            info = as_dict(raid.get('instance'))
            raid_name = info.get('name')
            if not raid_name:
                continue
            difficulty, mode = select_difficulty(raid.get('modes'))
            if not mode:
                continue
            progress = as_dict(mode.get('progress'))
            completed = progress.get('completed_count')
            total = progress.get('total_count')
            if not isinstance(completed, int) or not isinstance(total, int) or total <= 0:
                print(f'WARN Blizzard raid progress missing counts: {raid_name} ({difficulty})')
                continue
            # Don't imply a zero is a confirmed run. No boss kills -> omit from history.
            if completed <= 0:
                continue
            bosses = []
            for row in as_list(progress.get('encounters')):
                row = as_dict(row)
                encounter = as_dict(row.get('encounter'))
                if encounter.get('name'):
                    bosses.append({'name': encounter['name'],
                                   'completedCount': row.get('completed_count'),
                                   'lastKillTimestamp': row.get('last_kill_timestamp')})
            entry = {'name': raid_name, 'difficulty': difficulty,
                     'mythicKills': completed if difficulty == 'MYTHIC' else None,
                     'heroicKills': completed if difficulty == 'HEROIC' else None,
                     'completedBosses': completed, 'totalBosses': total,
                     'note': f'{completed}/{total} {"M" if difficulty == "MYTHIC" else "H"}',
                     'source': 'Blizzard', 'bosses': bosses}
            result.setdefault(exp_name, []).append(entry)
    return result


def sync_blizzard(data):
    access = oauth('https://oauth.battle.net/token', 'BLIZZARD_CLIENT_ID', 'BLIZZARD_CLIENT_SECRET')
    base = f'https://eu.api.blizzard.com/profile/wow/character/{REALM}/{NAME}'
    headers = {'Authorization': 'Bearer ' + access}
    def get(path):
        return http_json(base + path + '?namespace=profile-eu&locale=en_GB', headers)
    profile = get('')
    data['character'] = {'name': profile.get('name'), 'level': profile.get('level'),
                         'class': as_dict(profile.get('character_class')).get('name'),
                         'race': as_dict(profile.get('race')).get('name'),
                         'itemLevel': profile.get('equipped_item_level')}
    data['achievementPoints'] = profile.get('achievement_points')
    try:
        ach = get('/achievements')
        cutting = []
        for row in as_list(ach.get('achievements')):
            row = as_dict(row)
            a = as_dict(row.get('achievement'))
            name = a.get('name') or ''
            if name.lower().startswith('cutting edge:'):
                aid = a.get('id')
                timestamp = row.get('completed_timestamp')
                # Keep raw API timestamps; avoid treating future timestamps as verified.
                now_ms = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
                verified = isinstance(timestamp, (int, float)) and 0 < timestamp <= now_ms
                cutting.append({'name': name, 'tierId': str(aid), 'verified': verified,
                                'note': str(timestamp or ''),
                                'url': f'https://www.wowhead.com/achievement={aid}'})
        data['cuttingEdgeAchievements'] = cutting
    except Exception as exc:
        print(f'WARN Blizzard achievements: {type(exc).__name__}: {exc}', file=sys.stderr)
    try:
        mounts = get('/collections/mounts')
        if isinstance(mounts.get('mounts'), list):
            data['characterMountCount'] = len(mounts['mounts'])
    except Exception as exc:
        print(f'WARN Blizzard mounts: {type(exc).__name__}: {exc}', file=sys.stderr)
    try:
        encounters = get('/encounters/raids')
        history = parse_encounters(encounters)
        print(f'OK Blizzard historical raids: {sum(map(len, history.values()))} raids across {len(history)} expansions')
        data['historicalRaidProgression'] = history
        progression = dict(as_dict(data.get('raidProgressionByExpansion')))
        grouped = dict(as_dict(progression.get('history')))
        for expansion, raids in history.items():
            if normalize(expansion) == 'midnight':
                continue
            grouped[expansion] = [{'season': None, 'seasonName': 'Historical Raids', 'raids': raids}]
        progression['history'] = grouped
        data['raidProgressionByExpansion'] = progression
    except Exception as exc:
        print(f'WARN Blizzard historical raids: {type(exc).__name__}: {exc}', file=sys.stderr)
    print('OK blizzard')


def sync_warcraftlogs(data):
    access = oauth('https://www.warcraftlogs.com/oauth/token',
                   'WARCRAFTLOGS_CLIENT_ID', 'WARCRAFTLOGS_CLIENT_SECRET')
    query = '''query($name:String!,$server:String!,$region:String!){characterData{character(name:$name,serverSlug:$server,serverRegion:$region){id name zoneRankings}}}'''
    result = http_json('https://www.warcraftlogs.com/api/v2/client',
                       {'Authorization': 'Bearer ' + access},
                       json_body={'query': query, 'variables': {'name': 'Draekhorr', 'server': REALM, 'region': 'EU'}})
    if result.get('errors'):
        raise RuntimeError('Warcraft Logs GraphQL errors: ' + str(result['errors'])[:400])
    char = as_dict(as_dict(as_dict(result.get('data')).get('characterData')).get('character'))
    if not char:
        raise RuntimeError('Character not found in Warcraft Logs')
    ranking = as_dict(char.get('zoneRankings'))
    parses = []
    for row in as_list(ranking.get('rankings')):
        row = as_dict(row)
        pct = row.get('rankPercent')
        if not isinstance(pct, (int, float)):
            continue
        name = as_dict(row.get('encounter')).get('name') or 'Boss'
        parses.append({'name': name, 'note': f'Rank percentile: {pct}', 'url': WCL_URL})
    data['warcraftLogs'] = {'profileUrl': WCL_URL,
                            'bestPerformanceAverage': ranking.get('bestPerformanceAverage'),
                            'medianPerformanceAverage': ranking.get('medianPerformanceAverage'),
                            'bossParses': parses}
    print('OK warcraftLogs')


def main():
    data = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    successes = 0
    for name, function in [('raiderio', sync_rio), ('warcraftLogs', sync_warcraftlogs), ('blizzard', sync_blizzard)]:
        try:
            function(data)
            successes += 1
        except Exception as exc:
            print(f'WARN {name}: {type(exc).__name__}: {exc}', file=sys.stderr)
    if successes == 0:
        raise SystemExit('ERROR: All API integrations failed; data.json untouched')
    data['updatedAt'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Wrote data.json')


if __name__ == '__main__':
    main()
