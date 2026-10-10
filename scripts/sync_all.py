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
                if 'raiderIo' in changes and isinstance(changes['raiderIo'], dict):
                    changes['raiderIo'] = {**(data.get('raiderIo') or {}), **changes['raiderIo']}
                data.update(changes)
            else:
                data[section] = {**data.get(section, {}), **changes}
            print(f'OK {section or "blizzard"}', flush=True)
            return True
    except Exception as exc:
        print(f'WARN {section or "blizzard"}: {type(exc).__name__}: {exc}', file=sys.stderr, flush=True)
    return False

def rio():
    """Fetch explicit season scores; never confuse highest historical with current."""
    fields = ("mythic_plus_scores_by_season:season-mn-2,"
              "mythic_plus_scores_by_season:season-mn-1,"
              "mythic_plus_best_runs,raid_progression")
    q = urllib.parse.urlencode({'region': REGION, 'realm': REALM, 'name': NAME, 'fields': fields})
    obj = request('https://raider.io/api/v1/characters/profile?' + q)
    seasons = obj.get('mythic_plus_scores_by_season') or []
    print('DIAG RIO season entries:', [
        {'season': str(x.get('season')), 'score_keys': list((x.get('scores') or {}).keys())}
        for x in seasons if isinstance(x, dict)
    ], flush=True)
    def score(season_id):
        for row in seasons:
            if not isinstance(row, dict):
                continue
            season = row.get('season')
            slug = season.get('slug') if isinstance(season, dict) else season
            if slug == season_id:
                return (row.get('scores') or {}).get('all')
        return None
    current_score = score('season-mn-2')
    previous_score = score('season-mn-1')
    if current_score is None:
        print('WARN RIO current season score unavailable; preserving prior score; raid data will still update', flush=True)
    runs = []
    for r in (obj.get('mythic_plus_best_runs') or []):
        url = r.get('url') or ''
        if '/season-mn-2/' not in url:
            continue
        runs.append({'name': f"{r.get('dungeon', 'Dungeon')} +{r.get('mythic_level', '?')}",
                     'note': f"Score: {r.get('score', 'N/A')} | Timed: {r.get('is_completed_within_time', r.get('num_keystone_upgrades', 0) > 0)}",
                     'url': url})
        if len(runs) >= 8:
            break
    # Raider.IO raid_progression is a mixed-season map. Use an explicit,
    # auditable slug allowlist instead of assuming all entries are current.
    # Unknown raids are retained separately for review, not misclassified.
    raid_meta = {
        'the-venomous-abyss': ('The Venomous Abyss', 'season-mn-2'),
        'the-tidebound-grotto': ('The Tidebound Grotto', 'season-mn-2'),
        'sporefall': ('Sporefall', 'season-mn-1'),
        'tier-mn-1': ('Midnight Season 1 Raid (name unverified)', 'season-mn-1'),
    }
    current, previous, unknown = [], [], []
    profile_url = 'https://raider.io/characters/eu/draenor/Draekhorr?season=season-mn-2'
    for slug, progress in (obj.get('raid_progression') or {}).items():
        if not isinstance(progress, dict):
            continue
        normalized = re.sub(r'[^a-z0-9]+', '-', slug.lower()).strip('-')
        name, season = raid_meta.get(normalized, (slug.replace('-', ' ').title(), None))
        summary = progress.get('summary')
        entry = {'name': name, 'note': summary or 'Progress unavailable',
                 'url': profile_url, 'sourceSlug': slug}
        if season == 'season-mn-2':
            current.append(entry)
        elif season == 'season-mn-1':
            previous.append(entry)
        else:
            unknown.append(entry)
    if not current:
        print('WARN RIO no classified current raids; preserving previous raid data', flush=True)
    # Old frontend expects raidProgression to be a flat list.
    # It now contains ONLY the explicitly classified current-season raids.
    result = {'raiderIo': {'currentSeason': 'season-mn-2',
                           'currentSeasonName': 'Midnight Season 2',
                           **({'currentSeasonScore': current_score, 'mythicPlusScore': current_score} if current_score is not None else {}),
                           'previousSeason': 'season-mn-1',
                           'previousSeasonName': 'Midnight Season 1',
                           **({'previousSeasonScore': previous_score} if previous_score is not None else {}),
                           'bestRuns': runs,
                           'profileUrl': profile_url},
              'raidProgression': current,
              'raidProgressionByExpansion': {
                  'currentSeason': {'expansion': 'Midnight', 'season': 'season-mn-2',
                                    'seasonName': 'Midnight Season 2', 'raids': current},
                  'history': {'Midnight': [
                      {'season': 'season-mn-1', 'seasonName': 'Midnight Season 1', 'raids': previous}]}},
              'unclassifiedRaidProgression': unknown,
              'raidSourceUrl': profile_url}
    if not current:
        result.pop('raidProgression', None)
        result.pop('raidProgressionByExpansion', None)
    return result

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
    # Diagnostic-only historical encounters request. Never print response values,
    # URLs, tokens, headers, character metadata, or raw JSON.
    try:
        encounters = get(f'/profile/wow/character/{REALM}/{NAME}/encounters/raids')
        if not isinstance(encounters, dict):
            print('DIAG BLIZZARD encounters root type:', type(encounters).__name__, flush=True)
        else:
            print('DIAG BLIZZARD encounters root keys:', sorted(encounters.keys()), flush=True)
            expansions = encounters.get('expansions')
            print('DIAG BLIZZARD expansions type:', type(expansions).__name__, flush=True)
            if isinstance(expansions, list):
                print('DIAG BLIZZARD expansions count:', len(expansions), flush=True)
                for i, item in enumerate(expansions[:3]):
                    print('DIAG BLIZZARD expansion', i, 'type:', type(item).__name__,
                          'keys:', sorted(item.keys()) if isinstance(item, dict) else '(not object)', flush=True)
                    if isinstance(item, dict):
                        instances = item.get('instances')
                        print('DIAG BLIZZARD instances type:', type(instances).__name__, flush=True)
                        if isinstance(instances, list) and instances:
                            first = instances[0]
                            print('DIAG BLIZZARD first instance type:', type(first).__name__,
                                  'keys:', sorted(first.keys()) if isinstance(first, dict) else '(not object)', flush=True)
                            if isinstance(first, dict):
                                modes = first.get('modes')
                                print('DIAG BLIZZARD modes type:', type(modes).__name__, flush=True)
                                if isinstance(modes, list) and modes:
                                    mode = modes[0]
                                    print('DIAG BLIZZARD first mode type:', type(mode).__name__,
                                          'keys:', sorted(mode.keys()) if isinstance(mode, dict) else '(not object)', flush=True)
            else:
                print('DIAG BLIZZARD expansions is not a list; historical parser intentionally skipped', flush=True)
    except Exception as exc:
        # HTTP errors may contain sensitive request details; log only status/type.
        status = getattr(exc, 'code', None)
        print('WARN Blizzard historical encounters:', type(exc).__name__,
              'HTTP status:', status if isinstance(status, int) else 'n/a', flush=True)
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
        if not isinstance(row, dict) or row.get('rankPercent') is None: continue
        cards.append({'name': row.get('encounter', {}).get('name', 'Boss') if isinstance(row.get('encounter'), dict) else 'Boss',
                      'note': f"Rank percentile: {row.get('rankPercent')}",
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
