"""Fetch Draekhorr's current guild without modifying unrelated WoW data."""
import json
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data.json'
PROFILE = 'https://raider.io/api/v1/characters/profile?' + urlencode({
    'region': 'eu', 'realm': 'draenor', 'name': 'Draekhorr', 'fields': 'guild'
})


def main():
    if not DATA.exists():
        print('WARN GUILD data.json missing')
        return
    try:
        request = Request(PROFILE, headers={'User-Agent': 'Draekhorr-WoW-Legacy/1.1.3'})
        with urlopen(request, timeout=25) as response:
            profile = json.load(response)
        raw = profile.get('guild') if isinstance(profile, dict) else None
        print('DIAG GUILD response type=' + type(raw).__name__)
        if isinstance(raw, dict):
            name = raw.get('name') or raw.get('guild_name')
            region = raw.get('region') or 'eu'
            realm = raw.get('realm') or 'draenor'
            url = raw.get('profile_url') or raw.get('profileUrl') or raw.get('url')
        elif isinstance(raw, str):
            name, region, realm, url = raw, 'eu', 'draenor', None
        else:
            print('WARN GUILD Raider.IO returned no guild; keeping last known guild if present')
            return
        if not isinstance(name, str) or not name.strip():
            print('WARN GUILD name missing; preserving data')
            return
        name = name.strip()
        if not isinstance(url, str) or not url.startswith('https://raider.io/guilds/'):
            url = 'https://raider.io/guilds/{}/{}/{}'.format(
                quote(str(region).lower(), safe=''), quote(str(realm), safe=''), quote(name, safe=''))
        data = json.loads(DATA.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('data.json root must be an object')
        data['guild'] = {'name': name, 'url': url}
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('OK GUILD ' + name)
    except Exception as exc:
        print('WARN GUILD {}: {}'.format(type(exc).__name__, exc))


if __name__ == '__main__':
    main()
