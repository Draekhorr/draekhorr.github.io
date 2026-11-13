#!/usr/bin/env python3
"""Sync WoW Forever from Raider.IO and Blizzard's currently undocumented Forever API.

Blizzard endpoints are experimental (November 2026). Missing/failed responses
never overwrite last-known-good verified fields. No HTML scraping.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'forever' / 'data.json'
RIO_API = 'https://forever.raider.io/api/v1/characters/profile'
RIO_PROFILE = 'https://forever.raider.io/characters/eu/normal/Draekhorr%20Healstappen'
BLIZZARD_PROFILE = 'https://worldofwarcraft.blizzard.com/en-gb/forever/eu/armory/character/draekhorr-healstappen'
CHARACTER = 'draekhorr-healstappen'
NAME = 'Draekhorr Healstappen'
SOURCE = 'Forever Raider.IO public character API'
BLIZZARD_API = f'https://eu.api.blizzard.com/profile/wow/character/{CHARACTER}'
BLIZZARD_PARAMS = {'namespace': 'profile-forever-eu', 'locale': 'en_GB'}


def text_value(value):
    if isinstance(value, dict):
        return text_value(value.get('name') or value.get('display_string') or value.get('value'))
    return str(value).strip() if isinstance(value, (str, int, float)) and not isinstance(value, bool) else None


def positive_number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 else None


def nonnegative_int(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def read_existing():
    try:
        data = json.loads(OUT.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def fetch_rio(session):
    for key in ('realm', 'ruleset'):
        try:
            response = session.get(RIO_API, params={'region': 'eu', key: 'normal', 'name': NAME}, timeout=20)
            print(f'DIAG FOREVER RIO status={response.status_code} lookup={key}')
            if response.status_code == 429:
                time.sleep(min(30, max(1, int(response.headers.get('Retry-After', '5')))))
                response = session.get(RIO_API, params={'region': 'eu', key: 'normal', 'name': NAME}, timeout=20)
            if response.ok:
                data = response.json()
                if isinstance(data, dict) and not data.get('error'):
                    name = text_value(data.get('name'))
                    surname = text_value(data.get('surname'))
                    if name and surname and surname.casefold() not in name.casefold():
                        name += ' ' + surname
                    if name and name.casefold() == NAME.casefold():
                        return data
                    print(f'WARN FOREVER unexpected RIO name={name!r}')
        except (requests.RequestException, ValueError) as exc:
            print(f'WARN FOREVER RIO {type(exc).__name__}: {exc}', file=sys.stderr)
    return None


def fetch_blizzard(session):
    client_id = os.getenv('BLIZZARD_CLIENT_ID')
    secret = os.getenv('BLIZZARD_CLIENT_SECRET')
    if not client_id or not secret:
        print('WARN FOREVER Blizzard credentials absent; skipping Blizzard profile')
        return {}
    try:
        auth = session.post('https://oauth.battle.net/token',
                            auth=(client_id, secret), data={'grant_type': 'client_credentials'}, timeout=20)
        auth.raise_for_status()
        token = auth.json()['access_token']
    except (requests.RequestException, ValueError, KeyError) as exc:
        print(f'WARN FOREVER Blizzard OAuth {type(exc).__name__}: {exc}', file=sys.stderr)
        return {}
    headers = {'Authorization': f'Bearer {token}'}
    result = {}
    for suffix, label in (('', 'profile'), ('/specializations', 'specializations'), ('/professions', 'professions')):
        try:
            response = session.get(BLIZZARD_API + suffix, params=BLIZZARD_PARAMS,
                                   headers=headers, timeout=20)
            print(f'DIAG FOREVER Blizzard {label} status={response.status_code}')
            if response.ok:
                body = response.json()
                if isinstance(body, dict):
                    result[label] = body
                    print(f'DIAG FOREVER Blizzard {label} keys={",".join(sorted(body.keys()))}')
        except (requests.RequestException, ValueError) as exc:
            print(f'WARN FOREVER Blizzard {label} {type(exc).__name__}: {exc}', file=sys.stderr)
    return result


def talent_distribution(spec):
    """Only accept explicit 3-tree spent-point totals; never infer 9/7/0 from ranks."""
    if not isinstance(spec, dict):
        return None
    for key in ('talent_trees', 'talentTrees'):
        trees = spec.get(key)
        if not isinstance(trees, list) or len(trees) != 3:
            continue
        counts = [t.get('spent_points') if isinstance(t, dict) else None for t in trees]
        if all(nonnegative_int(v) is not None for v in counts):
            return ' / '.join(map(str, counts))
    return None



def profession_entries(payload):
    """Accept only explicit primary-profession records with verified skill values."""
    if not isinstance(payload, dict):
        return []
    # Blizzard profiles commonly expose primaries as a list of profession objects.
    candidates = payload.get('primaries')
    if not isinstance(candidates, list):
        candidates = payload.get('primary_professions')
    if not isinstance(candidates, list):
        print('DIAG FOREVER professions: no recognized primary profession list')
        return []
    found = []
    for row in candidates:
        if not isinstance(row, dict):
            continue
        name = text_value(row.get('profession')) or text_value(row.get('name'))
        # The profession skill is a direct field only if the API provides it.
        skill = nonnegative_int(row.get('skill_points'))
        if skill is None:
            skill = nonnegative_int(row.get('skill'))
        maximum = nonnegative_int(row.get('max_skill_points'))
        if maximum is None:
            maximum = nonnegative_int(row.get('max_skill'))
        if not name or skill is None or maximum is None or maximum <= 0 or skill > maximum:
            continue
        found.append({'name': name, 'skill': skill, 'maxSkill': maximum})
    return found[:2]


def run():
    old = read_existing()
    session = requests.Session()
    session.headers.update({'User-Agent': 'DraekhorrForeverShowcase/2.8 (public character profile)', 'Accept': 'application/json'})
    rio = fetch_rio(session)
    blizzard = fetch_blizzard(session)
    profile = blizzard.get('profile', {})
    if profile:
        slug = text_value(profile.get('slug'))
        first = text_value(profile.get('name'))
        surname = text_value(profile.get('surname'))
        if (slug and slug.casefold() != CHARACTER) or (first and surname and f'{first} {surname}'.casefold() != NAME.casefold()):
            print('WARN FOREVER Blizzard character mismatch; discarding Blizzard data', file=sys.stderr)
            profile = {}
            blizzard.pop('specializations', None)
    if not rio and not profile:
        print('WARN FOREVER no verified API data; preserving existing snapshot', file=sys.stderr)
        return 1
    rio = rio or {}
    media = next((rio.get(k) for k in ('thumbnail_url', 'avatar_url', 'portrait_url')
                  if isinstance(rio.get(k), str) and rio[k].startswith('https://')), None)
    level = rio.get('level')
    if not isinstance(level, int) or isinstance(level, bool) or not (1 <= level <= 100):
        level = None
    blizz_level = profile.get('level')
    if isinstance(blizz_level, int) and not isinstance(blizz_level, bool) and 1 <= blizz_level <= 100:
        level = blizz_level
    ilvl = positive_number(profile.get('equipped_item_level')) or positive_number(profile.get('average_item_level'))
    spec = blizzard.get('specializations')
    talents = talent_distribution(spec)
    professions = profession_entries(blizzard.get('professions'))
    print(f'DIAG FOREVER verified primary professions={len(professions)}')
    guild = text_value(profile.get('guild')) or text_value(rio.get('guild'))
    record = {
        'name': NAME, 'level': level,
        'class': text_value(profile.get('character_class')) or text_value(rio.get('class')),
        'race': text_value(profile.get('race')) or text_value(rio.get('race')),
        'guild': guild,
        'honorableKills': nonnegative_int(rio.get('honorable_kills')),
        'makgoraKills': nonnegative_int(rio.get('makgora_kills')),
        'talents': talents,
        'professions': professions,
        'itemLevel': ilvl or next((positive_number(rio.get(k)) for k in ('item_level', 'itemLevel', 'equipped_item_level') if positive_number(rio.get(k)) is not None), None),
        'role': text_value(rio.get('active_spec_name')),
        'portraitUrl': media,
        'profileUrl': RIO_PROFILE,
        'armoryUrl': BLIZZARD_PROFILE,
        'source': SOURCE,
        'blizzardSource': 'Blizzard Forever profile API' if profile else None,
        'updatedAt': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
    }
    for field in ('level', 'class', 'race', 'guild', 'role', 'portraitUrl', 'honorableKills', 'makgoraKills', 'itemLevel', 'talents'):
        if record[field] is None and old.get('name') == NAME:
            record[field] = old.get(field)
    if not professions and old.get('name') == NAME and isinstance(old.get('professions'), list):
        record['professions'] = old['professions']
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('OK FOREVER profile saved fields=' + ','.join(k for k in ('level', 'class', 'race', 'guild', 'portraitUrl', 'honorableKills', 'makgoraKills', 'itemLevel', 'talents', 'professions') if record.get(k) is not None))
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
