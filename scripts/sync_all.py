#!/usr/bin/env python3
"""Best-effort API sync. No third-party dependencies. Never writes credentials."""
import base64, datetime, json, os, pathlib, re, sys, urllib.parse, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'data.json'
REGION, REALM, NAME = 'eu', 'draenor', 'draekhorr'
HEADERS = {'User-Agent': 'DraekhorrWoWLegacy/1.0 (personal non-commercial fan site)'}

def request(url, headers=None, body=None):
    h = {**HEADERS, **(headers or {})}
    if isinstance(body, dict):
        body = urllib.parse.urlencode(body).encode()
        h.setdefault('Content-Type', 'application/x-www-form-urlencoded')
    req = urllib.request.Request(url, data=body, headers=h)
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)

def update(section, fn, data):
    try:
        changes = fn()
        if changes is not None:
            if section is None:
                data.update(changes)
            else:
                data[section] = {**data.get(section, {}), **changes}
            print(f'OK {section or "blizzard"}', flush=True)
            return True
    except Exception as exc:
        print(f'WARN {section or "blizzard"}: {type(exc).__name__}: {exc}', file=sys.stderr, flush=True)
    return False

def rio():
    fields = 'mythic_plus_scores_by_season:current,mythic_plus_scores_by_season:previous,mythic_plus_best_runs,raid_progression'
    q = urllib.parse.urlencode({'region': REGION, 'realm': REALM, 'name': NAME, 'fields': fields})
    obj = request('https://raider.io/api/v1/characters/profile?' + q)
    seasons = obj.get('mythic_plus_scores_by_season') or []
    current = next((x for x in seasons if x.get('season') == 'current'), None)
    previous = next((x for x in seasons if x.get('season') == 'previous'), None)
    # API season values are often actual season IDs, so fallback to chronological order.
    if current is None and seasons: current = seasons[0]
    if previous is None and len(seasons) > 1: previous = seasons[1]
    runs = []
    for r in (obj.get('mythic_plus_best_runs') or [])[:8]:
        runs.append({'name': f"{r.get('dungeon', 'Dungeon')} +{r.get('mythic_level', '?')}",
                     'note': f"Score: {r.get('score', 'N/A')} | Timed: {r.get('num_keystone_upgrades', 0) > 0}",
                     'url': r.get('url')})
    raids = []
    for raid, progress in (obj.get('raid_progression') or {}).items():
        if not isinstance(progress, dict): continue
        raids.append({'name': raid.replace('-', ' ').title(), 'note': progress.get('summary', 'Progress unavailable'),
                      'url': obj.get('profile_url')})
    return {'raiderIo': {'mythicPlusScore': (current or {}).get('scores', {}).get('all'),
                          'previousSeasonScore': (previous or {}).get('scores', {}).get('all'),
                          'bestRuns': runs, 'profileUrl': obj.get('profile_url'),
                          'ranking': None},
            'raidProgression': raids, 'raidSourceUrl': obj.get('profile_url')}

def token(url, cid, secret):
    auth = base64.b64encode(f'{cid}:{secret}'.encode()).decode()
    return request(url, {'Authorization': 'Basic ' + auth}, {'grant_type': 'client_credentials'})['access_token']

def blizzard():
    cid, secret = os.getenv('BLIZZARD_CLIENT_ID'), os.getenv('BLIZZARD_CLIENT_SECRET')
    if not cid or not secret: raise RuntimeError('Missing Blizzard credentials')
    access = token('https://oauth.battle.net/token', cid, secret)
    headers = {'Authorization': 'Bearer ' + access}
    def get(path):
        return request('https://eu.api.blizzard.com' + path + ('&' if '?' in path else '?') + 'namespace=profile-eu&locale=en_GB', headers)
    changes = {}
    profile = get(f'/profile/wow/character/{REALM}/{NAME}')
    changes['character'] = {'name': profile.get('name'), 'level': profile.get('level'),
                            'class': (profile.get('character_class') or {}).get('name'),
                            'race': (profile.get('race') or {}).get('name'),
                            'itemLevel': profile.get('equipped_item_level')}
    changes['achievementPoints'] = profile.get('achievement_points')
    try:
        achievements = get(f'/profile/wow/character/{REALM}/{NAME}/achievements')
        ce = []
        for item in achievements.get('achievements', []):
            a = item.get('achievement') or {}
            title = a.get('name') or ''
            if re.search(r'^Cutting Edge:', title, re.I):
                ce.append({'name': title, 'tierId': str(a.get('id')), 'verified': True,
                           'note': str(item.get('completed_timestamp', '')),
                           'url': f"https://www.wowhead.com/achievement={a.get('id')}"})
        changes['cuttingEdgeAchievements'] = ce
    except Exception as exc:
        print(f'WARN Blizzard achievements: {exc}', file=sys.stderr)
    # Public character mount collection is NOT necessarily the full Battle.net account-wide collection.
    try:
        mounts = get(f'/profile/wow/character/{REALM}/{NAME}/collections/mounts')
        entries = mounts.get('mounts') or []
        changes['characterMountCount'] = len(entries)
        # Never populate accountWideMountCount from character collection.
    except Exception as exc:
        print(f'WARN Blizzard mounts: {exc}', file=sys.stderr)
    return changes

def wcl():
    cid, secret = os.getenv('WARCRAFTLOGS_CLIENT_ID'), os.getenv('WARCRAFTLOGS_CLIENT_SECRET')
    if not cid or not secret: raise RuntimeError('Missing Warcraft Logs credentials')
    access = token('https://www.warcraftlogs.com/oauth/token', cid, secret)
    query = '''query($name:String!, $server:String!, $region:String!) {
      characterData { character(name:$name, serverSlug:$server, serverRegion:$region) {
        id name zoneRankings } } }'''
    body = json.dumps({'query': query, 'variables': {'name': 'Draekhorr', 'server': REALM, 'region': 'EU'}}).encode()
    req = urllib.request.Request('https://www.warcraftlogs.com/api/v2/client', data=body,
             headers={**HEADERS, 'Authorization': 'Bearer ' + access, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response: result = json.load(response)
    if result.get('errors'): raise RuntimeError(str(result['errors'])[:500])
    character = ((result.get('data') or {}).get('characterData') or {}).get('character')
    if not character: raise RuntimeError('Character not found in Warcraft Logs')
    ranking = character.get('zoneRankings') or {}
    # GraphQL JSON scalar varies by zone and encounter; do not mislabel it as a lifetime average.
    rankings = ranking.get('rankings') or [] if isinstance(ranking, dict) else []
    cards = []
    for row in rankings[:12]:
        if not isinstance(row, dict): continue
        cards.append({'name': row.get('encounter', {}).get('name', 'Boss') if isinstance(row.get('encounter'), dict) else 'Boss',
                      'note': f"Rank percentile: {row.get('rankPercent', 'N/A')}",
                      'url': f"https://www.warcraftlogs.com/character/eu/{REALM}/{NAME}"})
    return {'profileUrl': f'https://www.warcraftlogs.com/character/eu/{REALM}/{NAME}',
            'bestPerformanceAverage': ranking.get('bestPerformanceAverage') if isinstance(ranking, dict) else None,
            'medianPerformanceAverage': ranking.get('medianPerformanceAverage') if isinstance(ranking, dict) else None,
            'bossParses': cards}

def main():
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    results = [update(None, rio, data), update('warcraftLogs', wcl, data), update(None, blizzard, data)]
    if any(results):
        data['updatedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        print('Wrote data.json')
    else:
        print('ERROR all APIs failed; preserving previous data.json', file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__': main()
