#!/usr/bin/env python3
"""Best-effort historical Warcraft Logs zone rankings backfill.

Only actual WCL healing rankings are stored. Existing records are retained when
WCL does not expose an older zone or a query fails. Run manually initially.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys

from sync_all import oauth, wcl_graphql, as_dict, as_list, OUT, REALM, WCL_URL


def type_name(node):
    node = node or {}
    while node.get('ofType'):
        node = node['ofType']
    return node.get('name') or ''


def schema_fields(access, typename):
    query = 'query($name:String!){__type(name:$name){fields{name args{name type{kind name ofType{kind name ofType{kind name}}}} type{kind name ofType{kind name}}}}}'
    obj = as_dict(wcl_graphql(access, query, {'name': typename}).get('__type'))
    return {f['name']: f for f in as_list(obj.get('fields'))}


def call_field(name, args):
    params = ','.join(f'{key}:{json.dumps(value)}' for key, value in args.items())
    return name + ('(' + params + ')' if params else '')


def discover_zones(access):
    world_fields = schema_fields(access, 'WorldData')
    if 'zones' not in world_fields:
        print('WARN WCL backfill: worldData.zones unavailable')
        return []
    zone_field = world_fields['zones']
    zone_args = {a['name']: a for a in zone_field.get('args', [])}
    # Obtain expansion identifiers dynamically; no hardcoded expansion IDs.
    expansions = []
    if 'expansions' in world_fields:
        try:
            response = wcl_graphql(access, '{worldData{expansions{id name}}}')
            expansions = [x for x in as_list(as_dict(response.get('worldData')).get('expansions')) if isinstance(x, dict)]
        except Exception as exc:
            print(f'WARN WCL expansion discovery: {type(exc).__name__}: {exc}')
    queries = []
    if 'expansionID' in zone_args:
        queries = [{'expansionID': int(x['id'])} for x in expansions if isinstance(x.get('id'), int)]
    elif 'expansionId' in zone_args:
        queries = [{'expansionId': int(x['id'])} for x in expansions if isinstance(x.get('id'), int)]
    else:
        required = [a for a in zone_args.values() if a.get('type', {}).get('kind') == 'NON_NULL']
        if not required:
            queries = [{}]
    if not queries:
        print('WARN WCL backfill: unable to enumerate zones using available API arguments')
        return []
    zones = {}
    for args in queries:
        try:
            response = wcl_graphql(access, '{worldData{' + call_field('zones', args) + '{id name}}}')
            for zone in as_list(as_dict(response.get('worldData')).get('zones')):
                if isinstance(zone, dict) and isinstance(zone.get('id'), int):
                    zones[zone['id']] = zone
        except Exception as exc:
            print(f'WARN WCL zone discovery {args}: {type(exc).__name__}: {exc}')
    print(f'DIAG WCL backfill discovered zones={len(zones)}')
    return list(zones.values())


def run():
    access = oauth('https://www.warcraftlogs.com/oauth/token',
                   'WARCRAFTLOGS_CLIENT_ID', 'WARCRAFTLOGS_CLIENT_SECRET')
    character_fields = schema_fields(access, 'Character')
    field = character_fields.get('zoneRankings')
    if not field:
        raise RuntimeError('WCL character.zoneRankings is unavailable')
    arg_names = {a['name'] for a in field.get('args', [])}
    zone_arg = next((key for key in ('zoneID', 'zoneId', 'zone') if key in arg_names), None)
    if not zone_arg:
        raise RuntimeError('WCL zoneRankings does not accept a zone identifier')
    if 'metric' not in arg_names:
        raise RuntimeError('WCL zoneRankings does not expose a healing metric')
    zones = discover_zones(access)
    if not zones:
        raise RuntimeError('No Warcraft Logs zones discovered; no data changed')
    data = json.loads(OUT.read_text(encoding='utf-8'))
    wcl = as_dict(data.get('warcraftLogs'))
    archive = as_dict(wcl.get('seasonArchive')).copy()
    dungeon_archive = dict(as_dict(wcl.get('dungeonArchive')))
    # Only classify zones as dungeons when their names match verified RIO runs.
    rio_runs = as_list(as_dict(data.get('raiderIo')).get('bestRuns'))
    def dungeon_name(value):
        import re
        return re.sub(r'[^a-z0-9]+', ' ', re.sub(r'\s*\+\d+\s*$', '', str(value or '').lower())).strip()
    verified_dungeons = {dungeon_name(r.get('name')) for r in rio_runs if isinstance(r, dict)}
    current_encounters = {x.get('encounterId') for x in as_list(wcl.get('bossParses')) if isinstance(x, dict)}
    added, skipped, errors = 0, 0, 0
    for zone in zones:
        zone_id, zone_name = zone['id'], zone.get('name') or f'Zone {zone["id"]}'
        key = f'wcl-zone-{zone_id}'
        if key in archive and as_list(as_dict(archive[key]).get('bossParses')):
            old = as_dict(archive[key])
            if dungeon_name(zone_name) in verified_dungeons:
                dungeon_archive[key] = old
            skipped += 1
            continue
        args = f'{zone_arg}:{zone_id},metric:hps'
        query = ('query($name:String!,$server:String!,$region:String!){characterData{'
                 'character(name:$name,serverSlug:$server,serverRegion:$region){'
                 f'zoneRankings({args})' + '}}}')
        try:
            response = wcl_graphql(access, query, {'name':'Draekhorr','server':REALM,'region':'EU'})
            char = as_dict(as_dict(response.get('characterData')).get('character'))
            rankings = as_dict(char.get('zoneRankings'))
            if str(rankings.get('metric') or 'hps').lower() != 'hps':
                skipped += 1
                continue
            parses = []
            for row in as_list(rankings.get('rankings')):
                row = as_dict(row)
                encounter = as_dict(row.get('encounter'))
                eid, name = encounter.get('id'), encounter.get('name')
                if not isinstance(eid, int) or not name:
                    continue
                pct = row.get('rankPercent')
                amount = row.get('bestAmount')
                hps = float(amount) if isinstance(amount, (int,float)) and amount > 0 else None
                if not isinstance(pct, (int,float)) and hps is None:
                    continue
                parses.append({'name':name,'encounterId':eid,'journalId':None,
                               'iconUrl':f'https://assets.rpglogs.com/img/warcraft/bosses/{eid}-icon.jpg?v=4',
                               'bestPercent':pct if isinstance(pct,(int,float)) else None,
                               'highestHps':hps,'url':WCL_URL})
            # Avoid saving an overlapping current-zone snapshot as historical.
            if not parses or (current_encounters and all(p['encounterId'] in current_encounters for p in parses)):
                skipped += 1
                continue
            archive[key] = {'name':zone_name, 'bossParses':parses, 'zoneId':zone_id,
                            'source':'Warcraft Logs', 'archivedAt':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}
            if dungeon_name(zone_name) in verified_dungeons:
                dungeon_archive[key] = archive[key]
                print(f'OK WCL dungeon zone={zone_id} name={zone_name!r}')
            added += 1
            print(f'OK WCL historical zone={zone_id} name={zone_name!r} bosses={len(parses)}')
        except Exception as exc:
            errors += 1
            print(f'WARN WCL historical zone={zone_id}: {type(exc).__name__}: {exc}',file=sys.stderr)
    changed_dungeons = dungeon_archive != as_dict(wcl.get('dungeonArchive'))
    wcl['seasonArchive'] = archive
    wcl['dungeonArchive'] = dungeon_archive
    data['warcraftLogs'] = wcl
    if added or changed_dungeons:
        OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'DIAG WCL backfill: added={added} existing_or_empty={skipped} errors={errors} archive={len(archive)}')


if __name__ == '__main__':
    run()
