#!/usr/bin/env python3
"""Validate one-file-per-person profiles and index them into Ren-Wen's derived SQLite DB."""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"person-[a-z0-9-]+")
DECIMAL_ID = re.compile(r"[1-9][0-9]*")


def canonical_name(profile: dict) -> str:
    n = profile['name']
    place = f"[{n['jiguan']['label']}] " if n.get('jiguan') else ''
    alias = f"（{n['parenthetical']['value']}）" if n.get('parenthetical') else ''
    return place + (n.get('surname') or '') + n['given'] + alias


def sui_age(birth_chinese_year: int | None, event_chinese_year: int | None) -> int | None:
    """Inputs are resolved Chinese civil-year labels, not Gregorian years or dates."""
    if type(birth_chinese_year) is not int or type(event_chinese_year) is not int:
        return None
    if birth_chinese_year < 1 or event_chinese_year < birth_chinese_year:
        return None
    return event_chinese_year - birth_chinese_year + 1


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_profile(p: dict) -> None:
    _require(p.get('schemaVersion') == 1, 'Unsupported profile version')
    _require(isinstance(p.get('id'), str) and ID.fullmatch(p['id']) is not None, 'Invalid person ID')
    _require(p.get('reviewStatus') in {'agent-proposed', 'reviewed', 'disputed'}, 'Invalid review status')
    if p['reviewStatus'] == 'reviewed':
        _require(bool(p.get('reviewedBy')), 'Reviewed profiles require the actual reviewer')
    sources = p.get('sources')
    _require(isinstance(sources, dict) and bool(sources), 'Evidence sources are required')
    for key, source in sources.items():
        u = urlparse(source.get('url', ''))
        _require(u.scheme in {'https', 'http'} and bool(u.netloc), f'Unsafe source URL: {key}')
        _require(bool(source.get('title')) and bool(source.get('locator')), f'Missing source locator: {key}')

    def ref(key: str | None) -> None:
        _require(key in sources, f'Unknown evidence source: {key}')

    n = p['name']
    _require(isinstance(n.get('surname'), (str, type(None))), 'Surname must be a string or null')
    _require(isinstance(n.get('given'), str) and bool(n['given'].strip()), 'Given name or attested name is required')
    ref(n['source'])
    if n.get('jiguan') is not None:
        _require(bool(n['jiguan'].get('label')), 'Empty native-place label')
        ref(n['jiguan']['source'])
    for kind in ('zi', 'hao', 'romanizations'):
        _require(isinstance(n.get(kind), list), f'{kind} must be a list')
        for item in n[kind]:
            _require(isinstance(item.get('value'), str) and bool(item['value'].strip()), f'Empty {kind}')
            ref(item['source'])
    if n.get('parenthetical'):
        preferred = n['parenthetical']
        _require(preferred.get('kind') in {'zi', 'hao'}, 'Parenthetical must identify zi or hao')
        _require(any(x['value'] == preferred.get('value') for x in n[preferred['kind']]), 'Selected name is not in its typed name list')

    life = p['life']
    for endpoint in ('birth', 'death'):
        record = life.get(endpoint)
        if record is None:
            continue
        year = record.get('chineseYear')
        _require(year is None or (type(year) is int and 1 <= year <= 9999), f'Invalid Chinese {endpoint} year')
        if year is not None:
            _require(record.get('precision') == 'year' and bool(record.get('basis')), 'Year precision and basis are required')
            ref(record.get('source'))
        if record.get('era'):
            _require(type(record.get('eraYear')) is int and record['eraYear'] > 0, 'Invalid era year')
    birth = (life.get('birth') or {}).get('chineseYear')
    death = (life.get('death') or {}).get('chineseYear')
    _require(birth is None or death is None or death >= birth, 'Death year precedes birth year')
    for claim in life.get('westernDates', []):
        _require(claim.get('event') in {'birth', 'death'} and claim.get('calendar') == 'gregorian', 'Unsupported Western date claim')
        _require(isinstance(claim.get('value'), str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', claim['value']) is not None, 'Use a complete ISO Gregorian date')
        date.fromisoformat(claim['value'])
        ref(claim['source'])
    for claim in life.get('reportedAges', []):
        _require(type(claim.get('value')) is int and claim['value'] >= 1 and claim.get('system') == 'sui', 'Invalid reported sui age')
        ref(claim['source'])
    _require(set(p['externalIds']) == {'cbdb', 'geni'}, 'Both CBDB and Geni slots are required, even when unresolved')
    for provider, x in p['externalIds'].items():
        value = x.get('id')
        _require(value is None or (isinstance(value, str) and DECIMAL_ID.fullmatch(value) is not None), f'{provider} ID must be a decimal string or null')
        _require(x.get('status') in {'not-searched', 'unresolved', 'candidate', 'matched'}, 'Invalid identity-match status')
        if value is not None:
            u = urlparse(x.get('url', ''))
            host = 'cbdb.fas.harvard.edu' if provider == 'cbdb' else 'www.geni.com'
            _require(u.scheme == 'https' and u.hostname == host, f'Unexpected {provider} URL')
            _require(bool(x.get('evidence')) and bool(x.get('method')), 'ID mappings need matching evidence')
            ref(x['source'])
            date.fromisoformat(x['checked'])
        _require(value is not None or x['status'] != 'matched', 'An absent ID cannot be matched')
    for account in p.get('accounts', []):
        ref(account['source'])


def load_profiles(root: Path = ROOT) -> list[dict]:
    directory = (root / 'data/people').resolve()
    index = json.loads((directory / 'index.json').read_text(encoding='utf-8'))
    _require(index.get('schemaVersion') == 1 and isinstance(index.get('profiles'), list), 'Invalid profile index')
    result, ids, mappings = [], set(), set()
    for filename in index['profiles']:
        _require(isinstance(filename, str) and re.fullmatch(r'person-[a-z0-9-]+\.json', filename) is not None, 'Invalid profile filename')
        path = (directory / filename).resolve()
        _require(path.parent == directory, 'Profile path escapes its directory')
        p = json.loads(path.read_text(encoding='utf-8'))
        validate_profile(p)
        _require(filename == p['id'] + '.json' and p['id'] not in ids, 'Duplicate or mismatched person ID')
        ids.add(p['id'])
        for provider, x in p['externalIds'].items():
            if x['id'] is not None:
                key = (provider, x['id'])
                _require(key not in mappings, 'External ID assigned to more than one person')
                mappings.add(key)
        result.append(p)
    return result


def index_db(path: Path, root: Path = ROOT) -> dict:
    """Augment an existing derived corpus DB; never modify source JSON or text."""
    profiles = load_profiles(root)
    _require(path.is_file(), 'Build the corpus DB first: python scripts/renwen.py build-db')
    db = sqlite3.connect(path)
    try:
        db.execute('PRAGMA foreign_keys=ON')
        with db:
            for p in profiles:
                _require(db.execute('SELECT type FROM entities WHERE id=?', (p['id'],)).fetchone() == ('person',), f"Profile has no person entity: {p['id']}")
            db.execute('CREATE TABLE IF NOT EXISTS person_profiles(id TEXT PRIMARY KEY REFERENCES entities(id), canonical_name TEXT NOT NULL, birth_chinese_year INTEGER, death_chinese_year INTEGER, metadata TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS person_external_ids(person_id TEXT REFERENCES person_profiles(id), provider TEXT NOT NULL, external_id TEXT, status TEXT NOT NULL, metadata TEXT NOT NULL, PRIMARY KEY(person_id,provider), UNIQUE(provider,external_id))')
            db.execute('CREATE TABLE IF NOT EXISTS person_names(person_id TEXT REFERENCES person_profiles(id), kind TEXT NOT NULL, value TEXT NOT NULL, metadata TEXT NOT NULL)')
            db.execute('DELETE FROM person_external_ids')
            db.execute('DELETE FROM person_names')
            db.execute('DELETE FROM person_profiles')
            encode = lambda obj: json.dumps(obj, ensure_ascii=False)
            for p in profiles:
                life = p['life']
                birth = (life.get('birth') or {}).get('chineseYear')
                death = (life.get('death') or {}).get('chineseYear')
                db.execute('INSERT INTO person_profiles VALUES(?,?,?,?,?)', (p['id'], canonical_name(p), birth, death, encode(p)))
                for provider, x in p['externalIds'].items():
                    db.execute('INSERT INTO person_external_ids VALUES(?,?,?,?,?)', (p['id'], provider, x['id'], x['status'], encode(x)))
                for kind in ('surname', 'given'):
                    if p['name'].get(kind):
                        db.execute('INSERT INTO person_names VALUES(?,?,?,?)', (p['id'], kind, p['name'][kind], encode({'source': p['name']['source']})))
                for kind in ('zi', 'hao', 'romanizations'):
                    for name in p['name'][kind]:
                        db.execute('INSERT INTO person_names VALUES(?,?,?,?)', (p['id'], kind, name['value'], encode(name)))
            db.execute('CREATE VIEW IF NOT EXISTS person_profile_summary AS SELECT id, canonical_name, birth_chinese_year, death_chinese_year, CASE WHEN birth_chinese_year IS NOT NULL AND death_chinese_year IS NOT NULL THEN death_chinese_year-birth_chinese_year+1 END AS sui_at_death FROM person_profiles')
            _require(not db.execute('PRAGMA foreign_key_check').fetchall(), 'Foreign-key check failed')
    finally:
        db.close()
    return {'profiles': len(profiles), 'database': str(path), 'derived': True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate')
    commands.add_parser('list')
    db = commands.add_parser('index-db')
    db.add_argument('--database', type=Path, default=ROOT / 'build/renwen.sqlite')
    args = parser.parse_args()
    try:
        if args.command == 'index-db':
            result = index_db(args.database)
        else:
            profiles = load_profiles()
            result = {'profiles': len(profiles), 'valid': True} if args.command == 'validate' else [
                {'id': p['id'], 'canonicalName': canonical_name(p), 'suiAtDeath': sui_age((p['life'].get('birth') or {}).get('chineseYear'), (p['life'].get('death') or {}).get('chineseYear'))} for p in profiles]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error) as error:
        parser.exit(1, f'Profile error: {error}\n')


if __name__ == '__main__':
    main()
