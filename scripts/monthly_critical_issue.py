#!/usr/bin/env python3
"""Create one GitHub issue for prior-month critical incidents, if any."""
import datetime as dt
import json
import os
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]

def request(method, path, token, payload=None):
    url = f'https://api.github.com{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'Draekhorr-Monitor/5.8',
        'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def main():
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    now = dt.datetime.now(dt.timezone.utc)
    end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last = (end - dt.timedelta(days=1)).replace(day=1)
    period = last.strftime('%Y-%m')
    title = f'Draekhorr API critical failures — {period}'
    state_file = ROOT / 'health_state.json'
    if not state_file.exists():
        print('No health history; no report')
        return
    state = json.loads(state_file.read_text(encoding='utf-8'))
    incidents = [i for i in state.get('incidents', [])
                 if last <= dt.datetime.fromisoformat(i['startedAt'].replace('Z', '+00:00')) < end]
    if not incidents:
        print(f'No critical incidents in {period}; no issue created')
        return
    # Avoid duplicate reports on workflow retries; search open AND closed issues.
    from urllib.parse import quote
    q = quote(f'repo:{repo} in:title "{title}"')
    matches = request('GET', f'/search/issues?q={q}&per_page=100', token).get('items', [])
    if any(item.get('title') == title for item in matches):
        print('Monthly report already exists; skipping')
        return
    lines = [f'## Critical API incidents — {period}', '',
             'Created only when a service failed three consecutive sync checks.', '',
             '| Service | Detected (UTC) | Resolved (UTC) | Last success (UTC) |',
             '| --- | --- | --- | --- |']
    for item in incidents:
        lines.append(f"| {item['service']} | {item['startedAt']} | {item.get('resolvedAt') or 'Still unresolved'} | {item.get('lastSuccess') or 'Unknown'} |")
    lines += ['', 'This issue is an automated monthly summary. Check Actions for diagnostics.',
              'GitHub email delivery depends on your notification and subscription settings.']
    issue = request('POST', f'/repos/{repo}/issues', token, {'title': title, 'body': '\n'.join(lines)})
    print('Created monthly issue:', issue['html_url'])
    # Assign owner to trigger a notification if owner is an individual with issue permissions.
    owner = repo.split('/')[0]
    try:
        request('POST', f"/repos/{repo}/issues/{issue['number']}/assignees", token,
                {'assignees': [owner]})
        print('Assigned issue to repository owner:', owner)
    except urllib.error.HTTPError as exc:
        print('WARN unable to assign issue:', exc.code, '(subscribe to issue/repo notifications)')

if __name__ == '__main__':
    main()
