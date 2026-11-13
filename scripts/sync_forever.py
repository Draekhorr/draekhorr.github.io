#!/usr/bin/env python3
"""Fetch public WoW Forever character data from the documented Raider.IO profile API.

No HTML scraping, no invented values, and no Retail character data. If the API
returns no usable profile, preserve an existing last-known-good snapshot.
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
API = 'https://forever.raider.io/api/v1/characters/profile'
PROFILE = 'https://forever.raider.io/characters/eu/normal/Draekhorr%20Healstappen'
NAME = 'Draekhorr Healstappen'


def text_value(value):
    if isinstance(value, dict):
        return text_value(value.get('name') or value.get('display_string') or value.get('value'))
    return str(value).strip() if isinstance(value, (str, int, float)) and not isinstance(value, bool) else None


def read_existing():
    try:
        return json.loads(OUT.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def fetch_profile():
    # Different public API revisions may use a ruleset rather than a realm.
    # Try only published character-profile endpoint parameters; do not scrape.
    attempts = [
        {'region': 'eu', 'realm': 'normal', 'name': NAME},
        {'region': 'eu', 'ruleset': 'normal', 'name': NAME},
    ]
    session = requests.Session()
    session.headers.update({'User-Agent': 'DraekhorrForeverShowcase/2.5 (GitHub Pages; public profile sync)', 'Accept': 'application/json'})
    for params in attempts:
        try:
            response = session.get(API, params=params, timeout=20)
            print(f'DIAG FOREVER API status={response.status_code} lookup={"realm" if "realm" in params else "ruleset"}')
            if response.status_code == 429:
                delay = min(30, max(1, int(response.headers.get('Retry-After', '5'))))
                time.sleep(delay)
                response = session.get(API, params=params, timeout=20)
            if response.status_code != 200:
                continue
            data = response.json()
            if not isinstance(data, dict) or data.get('error'):
                continue
            print('DIAG FOREVER profile fields=' + ','.join(sorted(data.keys())))
            return data
        except (requests.RequestException, ValueError) as exc:
            print(f'WARN FOREVER API {type(exc).__name__}: {exc}', file=sys.stderr)
    return None


def run():
    old = read_existing()
    profile = fetch_profile()
    if not profile:
        print('WARN FOREVER no verified Raider.IO profile response; preserving existing snapshot')
        return 1
    full_name = text_value(profile.get('name'))
    surname = text_value(profile.get('surname'))
    if full_name and surname and surname.casefold() not in full_name.casefold():
        full_name += ' ' + surname
    # Avoid accidentally caching an unrelated character from a fallback lookup.
    if not full_name or full_name.casefold() != NAME.casefold():
        print(f'WARN FOREVER unexpected profile name={full_name!r}; preserving snapshot', file=sys.stderr)
        return 1
    guild = text_value(profile.get('guild'))
    level = profile.get('level')
    if not isinstance(level, int) or isinstance(level, bool) or not (1 <= level <= 100):
        level = None
    media = profile.get('thumbnail_url') or profile.get('avatar_url') or profile.get('portrait_url')
    if not isinstance(media, str) or not media.startswith('https://'):
        media = None
    record = {
        'name': full_name,
        'level': level,
        'class': text_value(profile.get('class')),
        'race': text_value(profile.get('race')),
        'guild': guild,
        'honorableKills': profile.get('honorable_kills') if isinstance(profile.get('honorable_kills'), int) and not isinstance(profile.get('honorable_kills'), bool) and profile.get('honorable_kills') >= 0 else None,
        'makgoraKills': profile.get('makgora_kills') if isinstance(profile.get('makgora_kills'), int) and not isinstance(profile.get('makgora_kills'), bool) and profile.get('makgora_kills') >= 0 else None,
        # The verified public profile response does not expose talents.
        'talents': None,
        # Item level is only used when the API explicitly supplies it.
        'itemLevel': next((profile[k] for k in ('item_level', 'itemLevel', 'equipped_item_level') if isinstance(profile.get(k), (int, float)) and not isinstance(profile.get(k), bool) and profile[k] > 0), None),
        'role': text_value(profile.get('active_spec_name')),
        'portraitUrl': media,
        'profileUrl': PROFILE,
        'source': 'Forever Raider.IO public character API',
        'updatedAt': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
    }
    # Preserve existing verified values if a response temporarily omits fields.
    for field in ('level', 'class', 'race', 'guild', 'role', 'portraitUrl', 'honorableKills', 'makgoraKills', 'itemLevel'):
        if record[field] is None and old.get('source') == record['source']:
            record[field] = old.get(field)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('OK FOREVER profile saved fields=' + ','.join(k for k in ('level','class','race','guild','role','portraitUrl','honorableKills','makgoraKills','itemLevel') if record.get(k) is not None))
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
