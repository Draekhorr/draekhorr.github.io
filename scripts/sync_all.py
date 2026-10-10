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
# Current/previous season IDs are resolved from Raider.IO at runtime.
# Never infer the active season from the character's highest score.
WCL_URL = f'https://www.warcraftlogs.com/character/{REGION}/{REALM}/{NAME}'
USER_AGENT = 'DraekhorrWoWLegacy/4.9'

# Raid slug metadata is a verified historical mapping, not season detection.
# Unknown/new raids stay unclassified until their season is confirmed.
RAID_SEASONS = {
    'the-venomous-abyss': ('season-mn-2', 'The Venomous Abyss'),
    'the-tidebound-grotto': ('season-mn-2', 'The Tidebound Grotto'),
    'sporefall': ('season-mn-1', 'Sporefall'),
    'tier-mn-1': ('season-mn-1', 'Tier MN 1 (unresolved raid label)'),
}


def season_label(identifier):
    match = re.fullmatch(r'season-(.+)-(\d+)', str(identifier or ''))
    if not match:
        return str(identifier or 'Season unavailable')
    expansion, number = match.groups()
    known = {'mn': 'Midnight', 'tww': 'The War Within', 'df': 'Dragonflight',
             'sl': 'Shadowlands', 'bfa': 'Battle for Azeroth'}
    return f"{known.get(expansion, expansion.upper())} Season {number}"


def season_expansion(identifier):
    label = season_label(identifier)
    return label.rsplit(' Season ', 1)[0] if ' Season ' in label else 'Unknown expansion'


def profile_url(season=None):
    base = f'https://raider.io/characters/{REGION}/{REALM}/Draekhorr'
    return base + ('?season=' + urllib.parse.quote(season) if season else '')


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


def score_for(payload, season=None):
    rows = [as_dict(x) for x in as_list(as_dict(payload).get('mythic_plus_scores_by_season'))]
    for row in rows:
        if season is None or row.get('season') == season:
            value = as_dict(row.get('scores')).get('all')
            if isinstance(value, (int, float)):
                return value
    return None


def rio_profile(fields):
    url = 'https://raider.io/api/v1/characters/profile?' + urllib.parse.urlencode({
        'region': REGION, 'realm': REALM, 'name': NAME, 'fields': fields
    })
    return http_json(url)


def season_record(payload):
    rows = [as_dict(x) for x in as_list(as_dict(payload).get('mythic_plus_scores_by_season'))]
    for row in rows:
        if isinstance(row.get('season'), str) and row['season']:
            return row
    return None


def sync_rio(data):
    rio = dict(as_dict(data.get('raiderIo')))
    current_record = previous_record = None
    # Raider.IO resolves the active and preceding seasons, including expansion boundaries.
    # Independent calls prevent an unsupported field from suppressing the other data.
    for tag in ('current', 'previous'):
        try:
            result = rio_profile('mythic_plus_scores_by_season:' + tag)
            record = season_record(result)
            if tag == 'current':
                current_record = record
            else:
                previous_record = record
            print(f"DIAG RIO {tag} season={record.get('season') if record else 'unavailable'}")
        except Exception as exc:
            print(f'WARN RIO {tag} season lookup: {type(exc).__name__}: {exc}')

    # Never guess the current season from previous-season score or best historical score.
    current = current_record.get('season') if current_record else None
    previous = previous_record.get('season') if previous_record else None
    if current and previous == current:
        previous = None
    if not current:
        print('WARN RIO current season not resolved; preserving last verified season metadata')
        current = rio.get('currentSeason')
    if not previous:
        # Subtract one only *within* an expansion. Season 1 requires provider metadata.
        match = re.fullmatch(r'(season-.+)-(\d+)', current or '')
        if match and int(match.group(2)) > 1:
            previous = f'{match.group(1)}-{int(match.group(2))-1}'
        else:
            previous = rio.get('previousSeason')

    current_score = score_for({'mythic_plus_scores_by_season': [current_record]}, current) if current_record else None
    previous_score = score_for({'mythic_plus_scores_by_season': [previous_record]}, previous) if previous_record else None
    if current:
        rio.update({'currentSeason': current, 'currentSeasonName': season_label(current),
                    'profileUrl': profile_url(current)})
    if previous:
        rio.update({'previousSeason': previous, 'previousSeasonName': season_label(previous)})
    if current_score is not None:
        rio['currentSeasonScore'] = current_score
        rio['mythicPlusScore'] = current_score
        rio['currentSeasonScoreVerified'] = True
    else:
        # Avoid displaying stale values as verified for a newly detected season.
        if current and current != as_dict(data.get('raiderIo')).get('currentSeason'):
            rio['currentSeasonScore'] = None
            rio['mythicPlusScore'] = None
        rio['currentSeasonScoreVerified'] = False
        print('WARN RIO current score unavailable; not substituting an old season score')
    if previous_score is not None:
        rio['previousSeasonScore'] = previous_score
    elif previous and previous != as_dict(data.get('raiderIo')).get('previousSeason'):
        rio['previousSeasonScore'] = None
    scores = [v for v in (current_score, previous_score, rio.get('bestHistoricalScore'))
              if isinstance(v, (int, float))]
    if scores:
        rio['bestHistoricalScore'] = max(scores)

    # Request raid progress and runs separately from season discovery.
    try:
        payload = rio_profile('mythic_plus_best_runs,raid_progression')
    except Exception as exc:
        print(f'WARN RIO raid/run lookup: {type(exc).__name__}: {exc}')
        data['raiderIo'] = rio
        return
    if current and isinstance(payload.get('mythic_plus_best_runs'), list):
        runs = []
        for item in payload['mythic_plus_best_runs']:
            run = as_dict(item)
            link = run.get('url') or ''
            if f'/{current}/' not in link:
                continue
            runs.append({'name': f"{run.get('dungeon', 'Dungeon')} +{run.get('mythic_level', '?')}",
                         'note': f"Score: {run.get('score', 'N/A')} | Timed: {run.get('is_completed_within_time', 'N/A')}",
                         'url': link})
        rio['bestRuns'] = runs
    data['raiderIo'] = rio

    raw = as_dict(payload.get('raid_progression'))
    current_raids, previous_raids, unknown = [], [], []
    history_by_expansion = {}
    for slug, progress in raw.items():
        key = normalize(slug)
        season, name = RAID_SEASONS.get(key, (None, str(slug).replace('-', ' ').title()))
        entry = {'name': name, 'note': as_dict(progress).get('summary') or '',
                 'url': profile_url(current), 'source': 'Raider.IO', 'sourceSlug': slug}
        if season and current and season == current:
            current_raids.append(entry)
        elif season:
            expansion = season_expansion(season)
            groups = history_by_expansion.setdefault(expansion, {})
            groups.setdefault(season, []).append(entry)
            if season == previous:
                previous_raids.append(entry)
        else:
            unknown.append(entry)
    if raw:
        data['raidProgression'] = current_raids
        data['unclassifiedRaidProgression'] = unknown
    progression = dict(as_dict(data.get('raidProgressionByExpansion')))
    if current:
        progression['currentSeason'] = {'expansion': season_expansion(current), 'season': current,
                                        'seasonName': season_label(current), 'raids': current_raids}
    history = dict(as_dict(progression.get('history')))
    for expansion, seasons in history_by_expansion.items():
        history[expansion] = [{'season': season, 'seasonName': season_label(season), 'raids': raids}
                              for season, raids in seasons.items()]
    progression['history'] = history
    data['raidProgressionByExpansion'] = progression
    data['raidSourceUrl'] = profile_url(current)
    print(f'OK raiderio: current={current} score={current_score}; previous={previous} score={previous_score}; current raids={len(current_raids)}')


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


def wcl_graphql(access, query, variables=None):
    result = http_json('https://www.warcraftlogs.com/api/v2/client',
                       {'Authorization': 'Bearer ' + access},
                       json_body={'query': query, 'variables': variables or {}})
    if result.get('errors'):
        raise RuntimeError(str(result['errors'])[:450])
    return as_dict(result.get('data'))


def blizzard_encounter_icon(journal_id, blizzard_access):
    """Use official Blizzard journal encounter media when available.

    Media is optional: never guess an image URL or expose the access token.
    """
    if not isinstance(journal_id, int) or journal_id <= 0 or not blizzard_access:
        return None
    endpoint = (f'https://eu.api.blizzard.com/data/wow/journal-encounter/{journal_id}/media'
                '?namespace=static-eu&locale=en_GB')
    try:
        payload = http_json(endpoint, {'Authorization': 'Bearer ' + blizzard_access})
        for asset in as_list(payload.get('assets')):
            asset = as_dict(asset)
            if str(asset.get('key', '')).lower() in ('icon', 'image', 'splash'):
                url = asset.get('value')
                if isinstance(url, str) and url.startswith('https://'):
                    return url
    except Exception:
        pass
    return None


def sync_warcraftlogs(data):
    """Sync verified WCL healing rankings; investigate media/HPS without fabricating values.

    The public zoneRankings payload is JSON and does not necessarily contain a
    zone ID, HPS amount, or an image URL. We preserve known-good values and log
    only schema/key metadata, never access tokens or private reports.
    """
    access = oauth('https://www.warcraftlogs.com/oauth/token',
                   'WARCRAFTLOGS_CLIENT_ID', 'WARCRAFTLOGS_CLIENT_SECRET')
    variables = {'name': 'Draekhorr', 'server': REALM, 'region': 'EU'}

    def rankings(healing):
        field = 'zoneRankings(metric: hps)' if healing else 'zoneRankings'
        query = ('query($name:String!,$server:String!,$region:String!){'
                 'characterData{character(name:$name,serverSlug:$server,'
                 'serverRegion:$region){id name ' + field + '}}}')
        payload = wcl_graphql(access, query, variables)
        char = as_dict(as_dict(payload.get('characterData')).get('character'))
        if not char:
            raise RuntimeError('Character not found in Warcraft Logs')
        return as_dict(char.get('zoneRankings'))

    try:
        ranking = rankings(True)
        healing = True
    except Exception as exc:
        print(f'WARN WCL healing rankings: {type(exc).__name__}: {exc}', file=sys.stderr)
        ranking = rankings(False)
        healing = False

    rows = [as_dict(x) for x in as_list(ranking.get('rankings'))]
    if rows:
        print('DIAG WCL ranking keys=' + ','.join(sorted(ranking.keys())))
        print('DIAG WCL boss keys=' + ','.join(sorted(rows[0].keys())))
        print('DIAG WCL encounter keys=' + ','.join(sorted(as_dict(rows[0].get('encounter')).keys())))
        print('DIAG WCL ranking metric=' + str(ranking.get('metric')) + ' requested_hps=' + str(healing))
        for r in rows[:8]:
            e = as_dict(r.get('encounter'))
            print('DIAG WCL sample boss=' + str(e.get('name')) + ' bestAmount=' + str(r.get('bestAmount')) + ' rankPercent=' + str(r.get('rankPercent')))

    # Try optional zone ID representations; not all WCL zoneRankings versions include one.
    zone = as_dict(ranking.get('zone'))
    zone_id = next((v for v in (zone.get('id'), ranking.get('zoneID'), ranking.get('zoneId'),
                                ranking.get('zone_id')) if isinstance(v, int)), None)
    journal_by_id = {}
    if zone_id is not None:
        try:
            metadata = wcl_graphql(access,
                'query($id:Int!){zoneData{zone(id:$id){encounters{id name journalID}}}}',
                {'id': zone_id})
            zone_info = as_dict(as_dict(metadata.get('zoneData')).get('zone'))
            for item in as_list(zone_info.get('encounters')):
                item = as_dict(item)
                if isinstance(item.get('id'), int) and isinstance(item.get('journalID'), int):
                    journal_by_id[item['id']] = item['journalID']
            print(f'DIAG WCL journal mapping={len(journal_by_id)}')
        except Exception as exc:
            print(f'WARN WCL zone metadata: {type(exc).__name__}: {exc}', file=sys.stderr)
    else:
        print('DIAG WCL zone ID not exposed in zoneRankings; cannot map journal media directly')

    # Introspection helps identify an authoritative route to encounter media.
    # It is a small, optional request; failures never stop the sync.
    try:
        schema = wcl_graphql(access,
            '{encounter:__type(name:"Encounter"){fields{name}} '
            'zone:__type(name:"Zone"){fields{name}}}')
        for label in ('encounter', 'zone'):
            names = [x.get('name') for x in as_list(as_dict(schema.get(label)).get('fields'))
                     if isinstance(x, dict) and isinstance(x.get('name'), str)]
            print(f'DIAG WCL schema {label} fields=' + ','.join(names[:45]))
    except Exception as exc:
        print(f'WARN WCL schema inspection: {type(exc).__name__}: {exc}', file=sys.stderr)

    blizzard_access = None
    if journal_by_id:
        try:
            blizzard_access = oauth('https://oauth.battle.net/token',
                                    'BLIZZARD_CLIENT_ID', 'BLIZZARD_CLIENT_SECRET')
        except Exception as exc:
            print(f'WARN Blizzard media authentication: {type(exc).__name__}: {exc}', file=sys.stderr)

    old_rows = {str(x.get('name', '')).casefold(): x
                for x in as_list(as_dict(data.get('warcraftLogs')).get('bossParses'))
                if isinstance(x, dict)}
    parses = []
    for row in rows:
        encounter = as_dict(row.get('encounter'))
        name = encounter.get('name')
        if not isinstance(name, str) or not name:
            continue
        old = old_rows.get(name.casefold(), {})
        percentile = row.get('rankPercent')
        # amount is only accepted if this was explicitly requested as healing/HPS.
        # Some WCL ranking variants omit amount, so we do not infer HPS from percentiles.
        # WCL ranking bestAmount is the best observed amount for the requested metric.
        # Only expose it as HPS when the query explicitly requested hps and
        # the returned ranking confirms that metric (or omits metric entirely).
        amount = row.get('bestAmount')
        reported_metric = str(ranking.get('metric') or '').lower()
        hps_metric_ok = healing and (not reported_metric or reported_metric == 'hps')
        hps = float(amount) if hps_metric_ok and isinstance(amount, (int, float)) and amount >= 0 else None
        if hps is None and isinstance(old.get('highestHps'), (int, float)):
            hps = old['highestHps']
        if not isinstance(percentile, (int, float)) and hps is None:
            continue
        icon = next((encounter[k] for k in ('iconUrl', 'imageUrl', 'icon')
                     if isinstance(encounter.get(k), str) and encounter[k].startswith('https://')), None)
        encounter_id = encounter.get('id')
        journal_id = encounter.get('journalID') or journal_by_id.get(encounter_id)
        if icon is None:
            icon = blizzard_encounter_icon(journal_id, blizzard_access)
        if icon is None and isinstance(old.get('iconUrl'), str) and old['iconUrl'].startswith('https://'):
            icon = old['iconUrl']
        parses.append({'name': name, 'encounterId': encounter_id,
                       'journalId': journal_id, 'iconUrl': icon,
                       'bestPercent': percentile if isinstance(percentile, (int, float)) else None,
                       'highestHps': hps, 'url': WCL_URL})
    if healing and str(ranking.get('metric') or '').lower() not in ('', 'hps'):
        print('WARN WCL requested hps but returned metric=' + str(ranking.get('metric')), file=sys.stderr)
    if not parses:
        raise RuntimeError('No usable Warcraft Logs boss rankings; preserving prior data')
    data['warcraftLogs'] = {'profileUrl': WCL_URL, 'bossParses': parses,
                           'healingMetricConfirmed': healing}
    icons = sum(bool(row.get('iconUrl')) for row in parses)
    hps_count = sum(row.get('highestHps') is not None for row in parses)
    print(f'OK warcraftLogs: bosses={len(parses)}, icons={icons}, HPS={hps_count}, healing={healing}')


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
