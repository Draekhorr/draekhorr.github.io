#!/usr/bin/env python3
"""Backfill verified Raider.IO seasonal scores and dungeon runs.

Never attach an unverified run to a historical season. Preserve archived data
when Raider.IO does not expose season-specific runs.
"""
import json
import re
from urllib.parse import urlparse, unquote
from sync_all import (OUT, as_dict, as_list, rio_profile, season_label,
                      season_expansion, run_clear_time_ms, run_icon_url)

CANDIDATES = {'mn': range(1, 5), 'tww': range(1, 5), 'df': range(1, 5),
              'sl': range(1, 5), 'bfa': range(1, 5), 'legion': range(1, 5)}


def verified_season(run):
    """Use explicit season metadata first; otherwise a URL path segment."""
    for field in ('season', 'season_slug', 'seasonSlug'):
        value = run.get(field)
        if isinstance(value, dict):
            value = value.get('slug') or value.get('name')
        if isinstance(value, str) and re.fullmatch(r'season-[a-z0-9-]+-\d+', value):
            return value
    url = run.get('url')
    if isinstance(url, str) and url.startswith('https://'):
        segments = [unquote(s).lower() for s in urlparse(url).path.split('/')]
        return next((s for s in segments if re.fullmatch(r'season-[a-z0-9-]+-\d+', s)), None)
    return None


def verified_runs(payload, season):
    results, unverified = [], 0
    for item in as_list(as_dict(payload).get('mythic_plus_best_runs')):
        run = as_dict(item)
        if verified_season(run) != season:
            unverified += 1
            continue
        dungeon, level, url = run.get('dungeon'), run.get('mythic_level'), run.get('url')
        if not isinstance(dungeon, str) or not isinstance(level, int) or not isinstance(url, str) or not url.startswith('https://'):
            continue
        results.append({'name': f'{dungeon} +{level}', 'score': run.get('score'),
                        'clearTimeMs': run_clear_time_ms(run),
                        'iconUrl': run_icon_url(run), 'url': url})
    return results, unverified


def run():
    data = json.loads(OUT.read_text(encoding='utf-8'))
    rio = as_dict(data.get('raiderIo')).copy()
    history = as_dict(rio.get('seasonHistory')).copy()
    candidates = {f'season-{prefix}-{n}' for prefix, nums in CANDIDATES.items() for n in nums}
    candidates.update(k for k in history if re.fullmatch(r'season-[a-z0-9-]+-\d+', k))
    candidates.update(s for s in (rio.get('currentSeason'), rio.get('previousSeason')) if s)
    scores = runs_count = errors = 0
    for season in sorted(candidates):
        entry = as_dict(history.get(season)).copy()
        try:
            response = rio_profile('mythic_plus_scores_by_season:' + season)
            matched = next((as_dict(r) for r in as_list(response.get('mythic_plus_scores_by_season'))
                            if as_dict(r).get('season') == season), None)
            score = as_dict(matched.get('scores')).get('all') if matched else None
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                entry['score'] = score
                scores += 1
        except Exception as exc:
            print(f'WARN RIO score season={season}: {type(exc).__name__}: {exc}')
        try:
            response = rio_profile('mythic_plus_best_runs:' + season)
            raw = as_list(response.get('mythic_plus_best_runs'))
            results, unverified = verified_runs(response, season)
            print(f'DIAG RIO runs season={season} returned={len(raw)} verified={len(results)} unverified={unverified}')
            if results:
                existing = {r['url']: r for r in as_list(entry.get('bestRuns')) if isinstance(r, dict) and r.get('url')}
                existing.update({r['url']: r for r in results})
                entry['bestRuns'] = list(existing.values())
                runs_count += 1
                print(f'OK RIO historical runs season={season} count={len(results)}')
        except Exception as exc:
            errors += 1
            print(f'WARN RIO runs season={season}: {type(exc).__name__}: {exc}')
        if entry.get('bestRuns') or isinstance(entry.get('score'), (int, float)):
            entry['name'] = season_label(season)
            entry['expansion'] = season_expansion(season)
            history[season] = entry
    rio['seasonHistory'] = history
    data['raiderIo'] = rio
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'DIAG RIO historical backfill scores={scores} seasons_with_runs={runs_count} errors={errors} archived={len(history)}')


if __name__ == '__main__':
    run()
