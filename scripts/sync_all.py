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
USER_AGENT = 'DraekhorrWoWLegacy/4.9.5'

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


# Explicitly verified icon path supplied for this dungeon. Other dungeons
# use an image URL only when the API actually returns one.
KNOWN_DUNGEON_ICONS = {
    'temple of sethraliss': 'https://cdn.raiderio.net/images/wow/icons/large/achievement_dungeon_templeofsethraliss.jpg',
}

def run_clear_time_ms(run):
    # Raider.IO best-runs responses typically include clear_time_ms.
    for field in ('clear_time_ms', 'clearTimeMs'):
        value = run.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
            return int(value)
    return None

def run_icon_url(run):
    for field in ('icon_url', 'iconUrl', 'dungeon_icon_url'):
        value = run.get(field)
        if isinstance(value, str) and value.startswith('https://'):
            return value
    dungeon = normalize(run.get('dungeon', '')).replace('-', ' ')
    return KNOWN_DUNGEON_ICONS.get(dungeon)


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
                         'score': run.get('score'),
                         'clearTimeMs': run_clear_time_ms(run),
                         'iconUrl': run_icon_url(run),
                         'url': link})
        previous_runs = {r.get('url'): r for r in as_list(rio.get('bestRuns')) if isinstance(r, dict)}
        for item in runs:
            old = previous_runs.get(item.get('url'), {})
            for key in ('clearTimeMs', 'iconUrl', 'score'):
                if item.get(key) is None and old.get(key) is not None:
                    item[key] = old[key]
        rio['bestRuns'] = runs
    data['raiderIo'] = rio

    raw = as_dict(payload.get('raid_progression'))
    progression = dict(as_dict(data.get('raidProgressionByExpansion')))
    history = dict(as_dict(progression.get('history')))
    old_current = as_dict(progression.get('currentSeason'))
    old_season = old_current.get('season')

    def add_history(expansion, season, raids):
        if not expansion or not season or not raids:
            return
        groups = [g for g in as_list(history.get(expansion)) if isinstance(g, dict)]
        match = next((g for g in groups if g.get('season') == season), None)
        if match is None:
            match = {'season': season, 'seasonName': season_label(season), 'raids': []}
            groups.insert(0, match)
        existing = {normalize(r.get('sourceSlug') or r.get('name')): r
                    for r in as_list(match.get('raids')) if isinstance(r, dict)}
        for raid in raids:
            key = normalize(raid.get('sourceSlug') or raid.get('name'))
            if key:
                existing[key] = raid
        match['raids'] = list(existing.values())
        history[expansion] = groups

    # Archive the last known current season BEFORE replacing it. This also works
    # when the expansion prefix changes (e.g. season-mn-3 -> season-next-1).
    if current and old_season and old_season != current:
        add_history(old_current.get('expansion') or season_expansion(old_season),
                    old_season, as_list(old_current.get('raids')))
        print(f'DIAG RIO season transition {old_season} -> {current}; archived previous current raids')

    current_raids, unknown = [], []
    for slug, progress in raw.items():
        info = as_dict(progress)
        key = normalize(slug)
        fallback_season, fallback_name = RAID_SEASONS.get(key, (None, str(slug).replace('-', ' ').title()))
        # Prefer explicit metadata supplied by the provider. Never infer a raid's
        # season from the active M+ season, its name, or a nonzero kill count.
        metadata_season = next((info.get(k) for k in ('season', 'season_slug', 'seasonSlug')
                                if isinstance(info.get(k), str) and
                                re.fullmatch(r'season-[a-z0-9-]+-\d+', info[k])), None)
        raid_season = metadata_season or fallback_season
        raid_name = info.get('name') if isinstance(info.get('name'), str) else fallback_name
        entry = {'name': raid_name, 'note': info.get('summary') or '',
                 'url': profile_url(current), 'source': 'Raider.IO', 'sourceSlug': slug}
        if raid_season and current and raid_season == current:
            current_raids.append(entry)
        elif raid_season:
            add_history(season_expansion(raid_season), raid_season, [entry])
        else:
            unknown.append(entry)

    # On temporary API failures, retain previously confirmed current raids only
    # if the active season did not change. Never show last season as current.
    if not raw and current and old_season == current:
        current_raids = as_list(old_current.get('raids'))
    if raw:
        data['unclassifiedRaidProgression'] = unknown
    if current:
        progression['currentSeason'] = {'expansion': season_expansion(current),
                                        'season': current, 'seasonName': season_label(current),
                                        'raids': current_raids}
        data['raidProgression'] = current_raids
    progression['history'] = history
    data['raidProgressionByExpansion'] = progression
    data['raidSourceUrl'] = profile_url(current)
    if unknown:
        print(f'WARN RIO {len(unknown)} raids lack verified season metadata; held as unclassified')
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
    previous_data = {'character': dict(as_dict(data.get('character')))}
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
    # V5.2: best-effort Blizzard character media and active specialization.
    # Keep the last verified portrait on transient API failures.
    character = data['character']
    active_spec = as_dict(profile.get('active_spec')).get('name')
    if isinstance(active_spec, str) and active_spec.strip():
        character['specialization'] = active_spec.strip()
    else:
        previous_spec = as_dict(as_dict(previous_data.get('character')).get('active_spec')).get('name')
        character['specialization'] = (as_dict(previous_data.get('character')).get('specialization')
                                       or previous_spec)
    old_portrait = as_dict(previous_data.get('character')).get('portraitUrl')
    if isinstance(old_portrait, str) and old_portrait.startswith('https://'):
        character['portraitUrl'] = old_portrait
    try:
        media = get('/character-media')
        assets = as_list(media.get('assets'))
        # Prefer the Blizzard headshot for this compact square portrait.
        # Full-body/inset renders become too small in a narrow banner.
        candidates = {}
        for asset in assets:
            asset = as_dict(asset)
            url = asset.get('value')
            if isinstance(url, str) and url.startswith('https://'):
                candidates[str(asset.get('key') or '').lower()] = url
        portrait = (candidates.get('avatar') or candidates.get('inset')
                    or candidates.get('main-raw') or candidates.get('main'))
        if portrait:
            character['portraitUrl'] = portrait
            print('OK Blizzard character portrait')
        else:
            print('WARN Blizzard character media: no usable portrait asset')
    except Exception as exc:
        print(f'WARN Blizzard character media: {type(exc).__name__}: {exc}', file=sys.stderr)

    # V5.5: audited raid boss kill counters. No assumed lifetime total.
    try:
        stats_payload = get('/achievements/statistics')
        entries = []
        def walk_stats(node, categories=(), depth=0):
            if depth > 20:
                return
            if isinstance(node, list):
                for child in node:
                    walk_stats(child, categories, depth + 1)
            elif isinstance(node, dict):
                category = as_dict(node.get('category'))
                category_name = category.get('name') if isinstance(category.get('name'), str) else None
                if not category_name and isinstance(node.get('name'), str) and not isinstance(node.get('quantity'), (int, float)):
                    category_name = node['name']
                path = categories + ((category_name,) if category_name else ())
                statistic = as_dict(node.get('statistic'))
                label = node.get('name') or statistic.get('name')
                identifier = node.get('id') or statistic.get('id')
                value = node.get('quantity', node.get('value'))
                if isinstance(label, str) and isinstance(value, (int, float)) and not isinstance(value, bool):
                    entries.append({'id': identifier, 'name': label, 'quantity': value,
                                    'categories': list(categories)})
                for key, child in node.items():
                    if isinstance(child, (list, dict)) and key not in ('statistic', 'category'):
                        walk_stats(child, path, depth + 1)
        walk_stats(stats_payload)
        # Dedupe repeated references by Blizzard statistic ID; never double count.
        unique = {}
        for entry in entries:
            key = str(entry['id']) if entry['id'] is not None else None
            if key is not None:
                unique.setdefault(key, entry)
        entries = list(unique.values())
        print(f'DIAG Blizzard lifetime statistics entries={len(entries)}')
        by_id = {str(row['id']): row for row in entries}
        lifetime = dict(as_dict(character.get('lifetimeStatistics')))
        for field, stat_id in [('totalDeaths', '60'), ('raidDeaths', '14784'),
                               ('dungeonDeaths', '14787'), ('fallingDeaths', '114')]:
            row = by_id.get(stat_id)
            if row and isinstance(row['quantity'], (int, float)) and row['quantity'] >= 0:
                lifetime[field] = int(row['quantity'])
        character['lifetimeStatistics'] = lifetime

        # All difficulty variants count: LFR, Normal, Heroic, Mythic, legacy 10/25.
        # Strictly select *individual raid boss* counters. Generic 'kills' and
        # instance-wide totals are deliberately not counted without verification.
        raid_hint = re.compile(r'raid|icecrown|dragon soul|highmaul|blackrock foundry|hellfire citadel|emerald nightmare', re.I)
        kill_hint = re.compile(r'\b(kills?|defeats?|victories|slain|destructions)\b', re.I)
        # Do not exclude 'player': legacy 10-player / 25-player raids are valid.
        exclude = re.compile(r'dungeon|world boss|trash|arena|battleground|\bpvp\b|\btotal\b|\bmost\b|\bhighest\b|raid bosses killed', re.I)
        candidates = []
        review_candidates = []
        for row in entries:
            label = row['name']
            path = ' / '.join(row['categories'])
            if not kill_hint.search(label) or row['quantity'] < 0:
                continue
            context = label + ' ' + path
            if exclude.search(context):
                continue
            if raid_hint.search(context):
                candidates.append(row)
            else:
                # Preserve ambiguous kill counters for manual classification;
                # never silently add them to the candidate sum.
                review_candidates.append(row)
        candidates.sort(key=lambda row: (str(row['categories']), row['name']))
        audit = {
            'description': 'Candidate per-boss raid kill counters across all difficulties. REVIEW REQUIRED; not an authoritative lifetime total.',
            'character': f'{NAME}-{REALM}-{REGION}',
            'candidateCount': len(candidates),
            'candidateSum': sum(int(row['quantity']) for row in candidates),
            'candidateStatistics': candidates,
            'unclassifiedKillStatistics': review_candidates,
            'unclassifiedCount': len(review_candidates),
            'warnings': [
                'Name/category matching can miss raids or include aggregate counters.',
                'Some Blizzard historic statistics may be missing or duplicated across categories.',
                'Do not publish candidateSum as verified lifetime Raid Boss Kills until audited.'
            ]
        }
        audit_path = ROOT / 'raid_kills_audit.json'
        audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f"DIAG Blizzard raid kill audit: candidates={len(candidates)} candidateSum={audit['candidateSum']} unclassified={audit['unclassifiedCount']} (UNVERIFIED)")
        print('OK Blizzard lifetime totalDeaths=' + str(lifetime.get('totalDeaths')) +
              ' raidDeaths=' + str(lifetime.get('raidDeaths')))
    except Exception as exc:
        print(f'WARN Blizzard lifetime statistics: {type(exc).__name__}: {exc}', file=sys.stderr)

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
        active_expansion = as_dict(progression.get('currentSeason')).get('expansion')
        for expansion, raids in history.items():
            # Current expansion raid kills are not necessarily current season.
            # Do not overwrite season-specific history with Blizzard's aggregate.
            groups = [g for g in as_list(grouped.get(expansion)) if isinstance(g, dict)]
            groups = [g for g in groups if g.get('season') is not None]
            if normalize(expansion) != normalize(active_expansion):
                groups.append({'season': None, 'seasonName': 'Historical Raids', 'raids': raids})
            grouped[expansion] = groups
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
    """Resolve actual Blizzard creature-display artwork for a journal encounter.

    Blizzard's journal-encounter endpoint references creatures[].creature_display;
    the creature-display media endpoint supplies the image URL. No guessed URLs.
    """
    if not isinstance(journal_id, int) or journal_id <= 0 or not blizzard_access:
        return None
    headers = {'Authorization': 'Bearer ' + blizzard_access}
    base = 'https://eu.api.blizzard.com/data/wow/'
    suffix = '?namespace=static-eu&locale=en_GB'
    try:
        journal = http_json(base + f'journal-encounter/{journal_id}' + suffix, headers)
    except Exception as exc:
        print(f'WARN WCL journal encounter {journal_id}: {type(exc).__name__}', file=sys.stderr)
        return None
    for creature in as_list(journal.get('creatures')):
        display = as_dict(as_dict(creature).get('creature_display'))
        display_id = display.get('id')
        if not isinstance(display_id, int) or display_id <= 0:
            continue
        try:
            media = http_json(base + f'media/creature-display/{display_id}' + suffix, headers)
            assets = [as_dict(a) for a in as_list(media.get('assets'))]
            for kind in ('portrait', 'zoom', 'rotate'):
                for asset in assets:
                    url = asset.get('value')
                    if asset.get('key') == kind and isinstance(url, str) and url.startswith('https://'):
                        return url
        except Exception as exc:
            print(f'WARN WCL creature display {display_id}: {type(exc).__name__}', file=sys.stderr)
    return None


def wcl_journal_ids(access, encounter_ids):
    """Get journal IDs directly by WCL encounter ID (no zone ID needed)."""
    mapping = {}
    ids = sorted({v for v in encounter_ids if isinstance(v, int) and v > 0})
    for start in range(0, len(ids), 8):
        batch = ids[start:start + 8]
        aliases = ' '.join(
            f'e{i}:encounter(id:{eid}){{id name journalID}}'
            for i, eid in enumerate(batch)
        )
        try:
            response = wcl_graphql(access, '{worldData{' + aliases + '}}')
            world = as_dict(response.get('worldData'))
            for i, eid in enumerate(batch):
                journal = as_dict(world.get(f'e{i}')).get('journalID')
                if isinstance(journal, int) and journal > 0:
                    mapping[eid] = journal
        except Exception as exc:
            print(f'WARN WCL encounter metadata: {type(exc).__name__}: {exc}', file=sys.stderr)
    print(f'DIAG WCL direct journal IDs={len(mapping)}/{len(ids)}')
    return mapping


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

    # WCL worldData.encounter(id) provides journalID directly. The previous
    # zoneRankings payload did not expose a zone ID, so zone lookup was skipped.
    journal_by_id = wcl_journal_ids(
        access, [as_dict(r.get('encounter')).get('id') for r in rows]
    )
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
        hps = float(amount) if hps_metric_ok and isinstance(amount, (int, float)) and amount > 0 else None
        if hps is None and isinstance(old.get('highestHps'), (int, float)):
            hps = old['highestHps']
        if not isinstance(percentile, (int, float)) and hps is None:
            continue
        icon = next((encounter[k] for k in ('iconUrl', 'imageUrl', 'icon')
                     if isinstance(encounter.get(k), str) and encounter[k].startswith('https://')), None)
        encounter_id = encounter.get('id')
        journal_id = encounter.get('journalID') or journal_by_id.get(encounter_id)
        # Warcraft Logs / RPGLogs boss CDN uses the WCL encounter ID.
        # The frontend already falls back to a placeholder if the image is missing.
        if icon is None and isinstance(encounter_id, int) and encounter_id > 0:
            icon = (f'https://assets.rpglogs.com/img/warcraft/bosses/'
                    f'{encounter_id}-icon.jpg?v=4')
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
    hps_count = sum(isinstance(row.get('highestHps'), (int, float)) and row['highestHps'] > 0 for row in parses)
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