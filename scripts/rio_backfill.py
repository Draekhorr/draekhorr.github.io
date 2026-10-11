#!/usr/bin/env python3
"""Best-effort Raider.IO historical M+ scores and best runs by verified season.

Run manually. Never assign current runs to an older season. Keep existing records
when the provider does not expose historical data.
"""
import json
import re
from sync_all import (OUT, as_dict, as_list, rio_profile, season_label,
                      season_expansion, run_clear_time_ms, run_icon_url)

# Candidate IDs only; the Raider.IO response must verify the season before use.
CANDIDATES = {
    'mn': range(1, 5), 'tww': range(1, 5), 'df': range(1, 5),
    'sl': range(1, 5), 'bfa': range(1, 5), 'legion': range(1, 5),
}


def verified_runs(payload, season):
    result = []
    for item in as_list(as_dict(payload).get('mythic_plus_best_runs')):
        run = as_dict(item)
        url = run.get('url')
        if not isinstance(url, str) or not re.search(r'/mythic-plus-runs/' + re.escape(season) + r'/', url):
            continue
        dungeon = run.get('dungeon')
        level = run.get('mythic_level')
        if not isinstance(dungeon, str) or not isinstance(level, int):
            continue
        result.append({'name': f'{dungeon} +{level}', 'score': run.get('score'),
                       'clearTimeMs': run_clear_time_ms(run),
                       'iconUrl': run_icon_url(run), 'url': url})
    return result


def run():
    data = json.loads(OUT.read_text(encoding='utf-8'))
    rio = as_dict(data.get('raiderIo')).copy()
    history = as_dict(rio.get('seasonHistory')).copy()
    candidates = {f'season-{prefix}-{n}' for prefix, numbers in CANDIDATES.items() for n in numbers}
    candidates.update(k for k in history if re.fullmatch(r'season-[a-z0-9-]+-\d+', k))
    candidates.update(s for s in (rio.get('currentSeason'), rio.get('previousSeason')) if s)
    found_scores = found_runs = errors = 0
    for season in sorted(candidates):
        entry = as_dict(history.get(season)).copy()
        try:
            response = rio_profile('mythic_plus_scores_by_season:' + season)
            rows = as_list(response.get('mythic_plus_scores_by_season'))
            matched = next((as_dict(row) for row in rows if as_dict(row).get('season') == season), None)
            score = as_dict(matched.get('scores')).get('all') if matched else None
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                entry['score'] = score
                found_scores += 1
        except Exception as exc:
            print(f'WARN RIO historical score {season}: {type(exc).__name__}: {exc}')
        try:
            response = rio_profile('mythic_plus_best_runs:' + season)
            runs = verified_runs(response, season)
            if runs:
                # Preserve already archived runs that are no longer returned.
                old = {x.get('url'): x for x in as_list(entry.get('bestRuns')) if isinstance(x, dict)}
                old.update({x['url']: x for x in runs})
                entry['bestRuns'] = list(old.values())
                found_runs += 1
                print(f'OK RIO historical runs season={season} count={len(runs)}')
        except Exception as exc:
            errors += 1
            print(f'WARN RIO historical runs {season}: {type(exc).__name__}: {exc}')
        if entry.get('bestRuns') or isinstance(entry.get('score'), (int, float)):
            entry['name'] = season_label(season)
            entry['expansion'] = season_expansion(season)
            history[season] = entry
    rio['seasonHistory'] = history
    data['raiderIo'] = rio
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'DIAG RIO historical backfill scores={found_scores} seasons_with_runs={found_runs} errors={errors} archived={len(history)}')


if __name__ == '__main__':
    run()
