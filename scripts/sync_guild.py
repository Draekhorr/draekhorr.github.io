"""Update only guild metadata in data.json using Raider.IO public profile API.
Preserve all other character and API data on failures.
"""
import json
import os
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data.json'
URL = 'https://raider.io/api/v1/characters/profile?' + urlencode({
    'region': 'eu', 'realm': 'draenor', 'name': 'Draekhorr', 'fields': 'guild'
})


def main():
    if not DATA.exists():
        print('WARN GUILD data.json missing; preserving existing data')
        return
    try:
        req = Request(URL, headers={'User-Agent': 'Draekhorr-WoW-Legacy/1.1.2'})
        with urlopen(req, timeout=20) as response:
            payload = json.load(response)
        guild = payload.get('guild')
        if not isinstance(guild, dict):
            print('WARN GUILD Raider.IO did not return guild metadata; preserving existing data')
            return
        name = guild.get('name')
        if not isinstance(name, str) or not name.strip():
            print('WARN GUILD no valid guild name; preserving existing data')
            return
        name = name.strip()
        region = str(guild.get('region') or 'eu').lower()
        realm = str(guild.get('realm') or 'draenor')
        url = guild.get('profile_url') or guild.get('profileUrl')
        if not isinstance(url, str) or not url.startswith('https://raider.io/guilds/'):
            url = f'https://raider.io/guilds/{quote(region, safe="")}/{quote(realm, safe="")}/{quote(name, safe="")}'
        data = json.loads(DATA.read_text(encoding='utf-8'))
        data['guild'] = {'name': name, 'url': url}
        DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'OK GUILD {name}')
    except Exception as exc:
        print(f'WARN GUILD {type(exc).__name__}: {exc}; preserving existing data')


if __name__ == '__main__':
    main()
