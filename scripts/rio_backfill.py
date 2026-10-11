#!/usr/bin/env python3
"""Raider.IO seasonal history. Discover provider slugs; retain verified data only.

Provider APIs may not expose historical best runs even when the website does.
No invented season entries or reassignment of current runs to old seasons.
"""
import json
import re
import sys
from urllib.parse import urlparse, parse_qs, unquote
from sync_all import (OUT, as_dict, as_list, rio_profile, http_json,
                      season_label, season_expansion, run_clear_time_ms, run_icon_url)

SLUG = re.compile(r'^season-[a-z0-9][a-z0-9.\-]*$', re.I)
EXPANSIONS = {'mn': 'Midnight', 'tww': 'The War Within', 'df': 'Dragonflight',
              'sl': 'Shadowlands', 'bfa': 'Battle for Azeroth', 'legion': 'Legion'}


def valid_slug(value):
    return isinstance(value, str) and bool(SLUG.fullmatch(value))


def slug_from(value):
    if isinstance(value, dict):
        for key in ('slug', 'season_slug', 'seasonSlug', 'season', 'id'):
            result = slug_from(value.get(key))
            if result:
                return result
        return None
    return value if valid_slug(value) else None


def discover(data):
    """Only API-confirmed slugs, including special events/patch variants."""
    found = {}
    rio = as_dict(data.get('raiderIo'))
    for key in ('currentSeason', 'previousSeason'):
        slug = slug_from(rio.get(key))
        if slug:
            found[slug] = {'name': rio.get(key + 'Name') or season_label(slug)}
    for slug, entry in as_dict(rio.get('seasonHistory')).items():
        if valid_slug(slug):
            found.setdefault(slug, as_dict(entry))
    # Public Raider.IO season listing, when supported by provider.
    for url in ('https://raider.io/api/v1/mythic-plus/seasons',
                'https://raider.io/api/v1/mythic-plus/static-data'):
        try:
            payload = http_json(url)
        except Exception as exc:
            print(f'WARN RIO season discovery {url}: {type(exc).__name__}: {exc}')
            continue
        collections = []
        if isinstance(payload, list):
            collections.append(payload)
        if isinstance(payload, dict):
            for key in ('seasons', 'mythic_plus_seasons', 'mythicPlusSeasons'):
                if isinstance(payload.get(key), list):
                    collections.append(payload[key])
            for expansion in as_list(payload.get('expansions')):
                expansion = as_dict(expansion)
                if isinstance(expansion.get('seasons'), list):
                    collections.append(expansion['seasons'])
        for collection in collections:
            for item in collection:
                item = as_dict(item)
                slug = slug_from(item)
                if not slug:
                    continue
                found.setdefault(slug, {'name': item.get('name') or item.get('title') or season_label(slug),
                                        'expansion': as_dict(item.get('expansion')).get('name') or item.get('expansion_name')})
        print(f'DIAG RIO season discovery endpoint={url} known={len(found)}')
    print(f'DIAG RIO discovered season slugs={len(found)}')
    return found


def verified_season(run):
    for key in ('season', 'season_slug', 'seasonSlug'):
        slug = slug_from(run.get(key))
        if slug:
            return slug
    url = run.get('url')
    if not isinstance(url, str) or not url.startswith('https://'):
        return None
    parsed = urlparse(url)
    for part in parsed.path.split('/'):
        part = unquote(part)
        if valid_slug(part):
            return part
    for candidate in parse_qs(parsed.query).get('season', []):
        if valid_slug(candidate):
            return candidate
    return None


def verified_runs(payload, season):
    rows = as_list(as_dict(payload).get('mythic_plus_best_runs'))
    result, unknown = [], 0
    for item in rows:
        run = as_dict(item)
        if verified_season(run) != season:
            unknown += 1
            continue
        dungeon, level, url = run.get('dungeon'), run.get('mythic_level'), run.get('url')
        if not isinstance(dungeon, str) or not isinstance(level, int) or not isinstance(url, str) or not url.startswith('https://'):
            continue
        result.append({'name': f'{dungeon} +{level}', 'score': run.get('score'),
                       'clearTimeMs': run_clear_time_ms(run), 'iconUrl': run_icon_url(run), 'url': url})
    return result, len(rows), unknown


def expansion_for(slug, entry):
    if isinstance(entry.get('expansion'), str) and entry['expansion']:
        return entry['expansion']
    for prefix, name in EXPANSIONS.items():
        if slug.startswith('season-' + prefix + '-'):
            return name
    if re.match(r'^season-7\.', slug):
        return 'Legion'
    return season_expansion(slug) if season_expansion(slug) != 'Unknown expansion' else 'Other'


def run():
    data = json.loads(OUT.read_text(encoding='utf-8'))
    rio = as_dict(data.get('raiderIo')).copy()
    history = as_dict(rio.get('seasonHistory')).copy()
    found = discover(data)
    scores = runs_count = errors = 0
    for season, metadata in sorted(found.items()):
        entry = as_dict(history.get(season)).copy()
        try:
            response = rio_profile('mythic_plus_scores_by_season:' + season)
            matched = next((as_dict(row) for row in as_list(response.get('mythic_plus_scores_by_season'))
                            if slug_from(as_dict(row).get('season')) == season), None)
            score = as_dict(matched.get('scores')).get('all') if matched else None
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                entry['score'] = score
                scores += 1
        except Exception as exc:
            errors += 1
            print(f'WARN RIO score {season}: {type(exc).__name__}: {exc}')
        try:
            response = rio_profile('mythic_plus_best_runs:' + season)
            runs, returned, unknown = verified_runs(response, season)
            print(f'DIAG RIO runs season={season} returned={returned} verified={len(runs)} unverified={unknown}')
            if runs:
                old = {r['url']: r for r in as_list(entry.get('bestRuns')) if isinstance(r, dict) and r.get('url')}
                old.update({r['url']: r for r in runs})
                entry['bestRuns'] = list(old.values())
                runs_count += 1
                print(f'OK RIO historical runs season={season} count={len(runs)}')
        except Exception as exc:
            errors += 1
            print(f'WARN RIO runs {season}: {type(exc).__name__}: {exc}')
        if entry.get('bestRuns') or isinstance(entry.get('score'), (int, float)):
            entry['name'] = entry.get('name') or metadata.get('name') or season_label(season)
            entry['expansion'] = expansion_for(season, {**metadata, **entry})
            history[season] = entry
    rio['seasonHistory'] = history
    data['raiderIo'] = rio
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'DIAG RIO historical backfill scores={scores} seasons_with_runs={runs_count} errors={errors} archived={len(history)}')


if __name__ == '__main__':
    run()
