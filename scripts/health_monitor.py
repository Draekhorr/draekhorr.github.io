#!/usr/bin/env python3
"""Run the existing WoW sync, persist per-service health and critical incidents."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'health_state.json'
SERVICES = {'raiderio': 'OK raiderio:', 'warcraftLogs': 'OK warcraftLogs:', 'blizzard': 'OK blizzard'}
CRITICAL_AFTER = 3


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def main():
    try:
        state = json.loads(STATE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        state = {}
    services = state.setdefault('services', {})
    incidents = state.setdefault('incidents', [])
    started = utcnow()
    run = subprocess.run([sys.executable, 'scripts/sync_all.py'], cwd=ROOT,
                         capture_output=True, text=True, check=False)
    if run.stdout:
        print(run.stdout, end='')
    if run.stderr:
        print(run.stderr, end='', file=sys.stderr)
    output = run.stdout + '\n' + run.stderr
    for key, marker in SERVICES.items():
        record = services.setdefault(key, {'consecutiveFailures': 0, 'lastSuccess': None})
        ok = marker in output and 'Wrote data.json' in output and run.returncode == 0
        if ok:
            record['consecutiveFailures'] = 0
            record['lastSuccess'] = started
            record['status'] = 'healthy'
            for incident in incidents:
                if incident.get('service') == key and not incident.get('resolvedAt'):
                    incident['resolvedAt'] = started
        else:
            record['consecutiveFailures'] = int(record.get('consecutiveFailures') or 0) + 1
            record['status'] = 'critical' if record['consecutiveFailures'] >= CRITICAL_AFTER else 'warning'
            if record['consecutiveFailures'] == CRITICAL_AFTER:
                incidents.append({'service': key, 'startedAt': started,
                                  'lastSuccess': record.get('lastSuccess'),
                                  'resolvedAt': None,
                                  'reason': 'No successful full sync for three consecutive scheduled runs'})
        record['lastChecked'] = started
        print(f"HEALTH {key}: {record['status']} failures={record['consecutiveFailures']}")
    state['lastCheck'] = started
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if run.returncode:
        print(f'WARN sync script exited {run.returncode}; health state was saved', file=sys.stderr)
    # Do not fail the workflow: state must be committed even when integrations fail.


if __name__ == '__main__':
    main()
