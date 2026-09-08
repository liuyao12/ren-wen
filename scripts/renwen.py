#!/usr/bin/env python3
"""Ren-Wen's dependency-free corpus, review, import and collation tools (Python 3.11+)."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import difflib
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PUNCTUATION = set('，。；：！？、「」『』（）《》〈〉〔〕【】…—')
IDENTIFIER = re.compile(r'^[A-Za-z0-9_-]{1,100}$')

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'

def inside(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes repository: {name}')
    return path

class TextIndex(HTMLParser):
    """Read simple working HTML; refuse executable content rather than rendering it."""
    allowed = {'p', 'span', 'a', 'i', 'b', 'em', 'strong', 'sup', 'sub', 'br'}
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.passages: dict[str, str] = {}
        self.mentions: dict[str, dict] = {}
        self.stack: list[tuple[str, dict]] = []
        self.text: list[str] = []
        self.feed(text)
        self.close()
        if self.stack:
            raise ValueError('Unclosed HTML elements')
    def handle_starttag(self, tag, attrs):
        if tag not in self.allowed:
            raise ValueError(f'Unsupported or unsafe HTML tag: {tag}')
        a = dict(attrs)
        for key, value in attrs:
            if key not in {'id', 'data-entity', 'href', 'lang'}:
                raise ValueError(f'Unsupported HTML attribute: {key}')
            if key == 'href' and not re.match(r'^https?://', value or ''):
                raise ValueError('Unsafe link URL')
        if 'id' in a:
            if a['id'] in self.ids:
                raise ValueError(f'Duplicate anchor: {a["id"]}')
            self.ids.add(a['id'])
        if tag == 'p':
            if not a.get('id') or any(t == 'p' for t, _ in self.stack):
                raise ValueError('Each non-nested paragraph needs a stable ID')
            self.passages[a['id']] = ''
        if 'data-entity' in a:
            if tag != 'span' or not a.get('id'):
                raise ValueError('Mention must be a span with an ID')
            p = next((v['id'] for t,v in reversed(self.stack) if t == 'p'), None)
            if p is None:
                raise ValueError('Mention outside paragraph')
            self.mentions[a['id']] = {'entity': a['data-entity'], 'passage': p, 'quote': ''}
        if tag != 'br':
            self.stack.append((tag, a))
    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            raise ValueError(f'Mismatched closing tag: {tag}')
        self.stack.pop()
    def handle_data(self, data):
        self.text.append(data)
        for tag, attrs in self.stack:
            if tag == 'p':
                self.passages[attrs['id']] += data
            if 'data-entity' in attrs:
                self.mentions[attrs['id']]['quote'] += data

def load_catalog(root: Path = ROOT) -> dict:
    return read_json(root / 'data/catalog.json')

def validate(root: Path = ROOT) -> dict:
    c = load_catalog(root)
    if c.get('schemaVersion') != 1:
        raise ValueError('Unsupported corpus schema version')
    for field in ('sources', 'entities', 'mentions', 'events', 'relations', 'textRelations', 'jurisdictions'):
        if not isinstance(c.get(field), list):
            raise ValueError(f'{field} must be an array')
        ids = [r['id'] for r in c[field]]
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate IDs in {field}')
    entities = {e['id']: e for e in c['entities']}
    sources = {s['id']: s for s in c['sources']}
    if c['defaultPerson'] not in entities or c['defaultWitness'] not in sources:
        raise ValueError('Invalid default person or witness')
    seen, indexes = {}, {}
    for s in c['sources']:
        for field, hash_field in [('text', 'sha256'), ('upstream', 'upstreamSha256')]:
            path = inside(root, s[field])
            if digest(path.read_bytes()) != s[hash_field]:
                raise ValueError(f'Checksum mismatch: {s[field]}')
        if not s.get('rights') or not s.get('punctuation'):
            raise ValueError('Source needs rights and punctuation provenance')
        working = TextIndex(inside(root, s['text']).read_text(encoding='utf-8'))
        original = TextIndex(inside(root, s['upstream']).read_text(encoding='utf-8'))
        if working.passages != original.passages:
            raise ValueError(f'Unrecorded textual change in {s["id"]}; update workflow required')
        indexes[s['id']] = working
        for mid, mention in working.mentions.items():
            if mid in seen:
                raise ValueError(f'Anchor reused across witnesses: {mid}')
            if mention['entity'] not in entities:
                raise ValueError(f'Unknown entity at {mid}')
            seen[mid] = (s['id'], mention)
    if set(seen) != {m['id'] for m in c['mentions']}:
        raise ValueError('Mention index and marked-up texts differ')
    for m in c['mentions']:
        wid, actual = seen[m['id']]
        if wid != m['witness'] or any(m[k] != actual[k] for k in ('entity','passage','quote')):
            raise ValueError(f'Incorrect mention index: {m["id"]}')
    for ev in c['events']:
        if ev['witness'] not in indexes or ev['passage'] not in indexes[ev['witness']].passages:
            raise ValueError(f'Missing event evidence: {ev["id"]}')
        for eid in ev['people'] + ev['places']:
            if eid not in entities:
                raise ValueError(f'Unknown event participant/place: {eid}')
        t=ev['time']
        if not isinstance(t['start'], int) or not isinstance(t['end'], int) or t['start'] > t['end'] or not t.get('original'):
            raise ValueError(f'Invalid event time: {ev["id"]}')
    for r in c['relations']:
        if r['subject'] not in entities or r['object'] not in entities or not r.get('evidence'):
            raise ValueError('Relation requires entities and evidence')
        for ev in r['evidence']:
            if ev['witness'] not in indexes or ev['passage'] not in indexes[ev['witness']].passages:
                raise ValueError('Unknown relation evidence')
    for r in c['textRelations']:
        if r['from'] not in sources or r['to'] not in sources:
            raise ValueError('Unknown text relationship endpoint')
    for e in entities.values():
        if e.get('life'):
            l=e['life']
            if l['birth'] > l['death'] or not l.get('source'):
                raise ValueError('Invalid or unsourced life dates')
        if e.get('point'):
            p=e['point'];x,y=p['coordinates']
            if not -180 <= x <= 180 or not -90 <= y <= 90 or not p.get('source'):
                raise ValueError('Invalid or unsourced coordinate')
    return {'sources':len(sources),'passages':sum(len(i.passages) for i in indexes.values()),'mentions':len(seen),'entities':len(entities),'events':len(c['events'])}

def validate_proposal(p: dict, c: dict) -> dict:
    if p.get('schemaVersion') != 1 or p.get('operation') != 'relink-mention':
        raise ValueError('Unsupported proposal format')
    source = next((s for s in c['sources'] if s['id'] == p.get('witness')), None)
    mention = next((m for m in c['mentions'] if m['id'] == p.get('mention')), None)
    if not source or not mention or mention['witness'] != source['id']:
        raise ValueError('Unknown witness or mention')
    if p.get('baseSha256') != source['sha256']:
        raise ValueError('Stale source version: rebase the proposal')
    if p.get('before') != mention['entity']:
        raise ValueError('Original identification does not match')
    if p.get('after') not in {e['id'] for e in c['entities']}:
        raise ValueError('Unknown target entity')
    if p['before'] == p['after']:
        raise ValueError('Unchanged identification')
    if len(str(p.get('reason','')).strip()) < 8:
        raise ValueError('Reason and evidence required')
    if not isinstance(p.get('id'), str) or not IDENTIFIER.fullmatch(p['id']):
        raise ValueError('Invalid proposal ID')
    if p.get('status') != 'proposed':
        raise ValueError('Only proposed changes may enter the queue')
    return p

def proposals(path: Path, c: dict) -> list[dict]:
    value = read_json(path)
    rows = value if isinstance(value,list) else [value]
    for p in rows:
        validate_proposal(p,c)
    if len({p['mention'] for p in rows}) != len(rows) or len({p['id'] for p in rows}) != len(rows):
        raise ValueError('Duplicate or competing proposals in one batch')
    return rows

def apply_proposals(path: Path, reviewer: str, root: Path = ROOT) -> dict:
    """Explicit editorial operation. All checks run before writing; keep changes in a Git worktree."""
    if not reviewer.strip():
        raise ValueError('A reviewer name is required')
    validate(root)
    c = load_catalog(root)
    rows = proposals(path,c)
    changes: dict[Path,str] = {}
    sources = {s['id']:s for s in c['sources']}
    for p in rows:
        s=sources[p['witness']];target=inside(root,s['text'])
        html=changes.get(target,target.read_text(encoding='utf-8'))
        pattern=rf'(<span\s+id="{re.escape(p["mention"])}"\s+data-entity="){re.escape(p["before"])}(")'
        html,count=re.subn(pattern,lambda m:m[1]+p['after']+m[2],html)
        if count != 1:
            raise ValueError('Unsupported span serialization: no changes were written')
        changes[target]=html
        m=next(m for m in c['mentions'] if m['id']==p['mention'])
        m.update(entity=p['after'],status='reviewed',reviewedBy=reviewer)
    for s in c['sources']:
        target=inside(root,s['text'])
        if target in changes:
            s['sha256']=digest(changes[target].encode('utf-8'))
    # Multi-file writes are not a filesystem transaction. Git review/commit is the publication boundary.
    for target,html in changes.items():
        target.write_text(html,encoding='utf-8')
    (root/'data/catalog.json').write_text(dump(c),encoding='utf-8')
    log=root/'data/reviews.jsonl'
    with log.open('a',encoding='utf-8') as f:
        for p in rows:
            f.write(json.dumps({**p,'status':'accepted','reviewedBy':reviewer,'reviewedAt':datetime.now(timezone.utc).isoformat()},ensure_ascii=False)+'\n')
    validate(root)
    return {'accepted':len(rows),'filesChanged':len(changes),'upstreamEdited':False}

def context(passage: str, root: Path = ROOT) -> dict:
    c=load_catalog(root)
    for s in c['sources']:
        idx=TextIndex(inside(root,s['text']).read_text(encoding='utf-8'))
        if passage in idx.passages:
            ms=[m for m in c['mentions'] if m['passage']==passage and m['witness']==s['id']]
            keys=list(idx.passages);i=keys.index(passage)
            return {'source':s,'passage':passage,'text':idx.passages[passage], 'neighbors':{k:idx.passages[k] for k in keys[max(0,i-1):i+2] if k!=passage},'mentions':ms,'entities':[e for e in c['entities'] if e['id'] in {m['entity'] for m in ms}],'events':[e for e in c['events'] if e['passage']==passage and e['witness']==s['id']]}
    raise ValueError('Unknown passage')

def build_db(output: Path, root: Path = ROOT) -> dict:
    validate(root); c=load_catalog(root);output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix('.building.sqlite')
    if temporary.exists(): temporary.unlink()
    db=sqlite3.connect(temporary)
    try:
        db.executescript('''
          PRAGMA foreign_keys=ON;
          CREATE TABLE sources(id TEXT PRIMARY KEY, work TEXT, metadata TEXT NOT NULL);
          CREATE TABLE entities(id TEXT PRIMARY KEY, type TEXT NOT NULL, label TEXT NOT NULL, metadata TEXT NOT NULL);
          CREATE TABLE passages(id TEXT PRIMARY KEY, witness TEXT REFERENCES sources(id), text TEXT NOT NULL);
          CREATE TABLE mentions(id TEXT PRIMARY KEY, witness TEXT REFERENCES sources(id), passage TEXT REFERENCES passages(id), entity TEXT REFERENCES entities(id), metadata TEXT NOT NULL);
          CREATE TABLE events(id TEXT PRIMARY KEY, witness TEXT REFERENCES sources(id), passage TEXT REFERENCES passages(id), start_year INTEGER, end_year INTEGER, metadata TEXT NOT NULL);
          CREATE TABLE relations(id TEXT PRIMARY KEY, subject TEXT REFERENCES entities(id), predicate TEXT, object TEXT REFERENCES entities(id), metadata TEXT NOT NULL);
          CREATE TABLE text_relations(id TEXT PRIMARY KEY, source_a TEXT REFERENCES sources(id), source_b TEXT REFERENCES sources(id), type TEXT, metadata TEXT NOT NULL);
          CREATE INDEX mentions_by_entity ON mentions(entity);
          CREATE INDEX events_by_year ON events(start_year,end_year);
        ''')
        for s in c['sources']:
            db.execute('INSERT INTO sources VALUES(?,?,?)',(s['id'],s['work'],dump(s)))
            idx=TextIndex(inside(root,s['text']).read_text(encoding='utf-8'))
            db.executemany('INSERT INTO passages VALUES(?,?,?)',[(pid,s['id'],text) for pid,text in idx.passages.items()])
        for e in c['entities']:
            db.execute('INSERT INTO entities VALUES(?,?,?,?)',(e['id'],e['type'],e['label'],dump(e)))
        for m in c['mentions']:
            db.execute('INSERT INTO mentions VALUES(?,?,?,?,?)',(m['id'],m['witness'],m['passage'],m['entity'],dump(m)))
        for e in c['events']:
            db.execute('INSERT INTO events VALUES(?,?,?,?,?,?)',(e['id'],e['witness'],e['passage'],e['time']['start'],e['time']['end'],dump(e)))
        for r in c['relations']:
            db.execute('INSERT INTO relations VALUES(?,?,?,?,?)',(r['id'],r['subject'],r['predicate'],r['object'],dump(r)))
        for r in c['textRelations']:
            db.execute('INSERT INTO text_relations VALUES(?,?,?,?,?)',(r['id'],r['from'],r['to'],r['type'],dump(r)))
        db.commit()
        if db.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('SQLite foreign-key validation failed')
    finally:
        db.close()
    temporary.replace(output)
    return {'database':str(output),'derived':True}

def inspect_xml(raw: bytes) -> dict:
    if len(raw)>5_000_000:
        raise ValueError('XML exceeds 5 MB pilot limit')
    text=raw.decode('utf-8-sig')
    if '\x00' in text or re.search(r'<!\s*(DOCTYPE|ENTITY)',text,re.I):
        raise ValueError('DTD, entity declarations and NULs are not accepted')
    tree=ET.fromstring(text)
    return {'sha256':digest(raw),'bytes':len(raw),'root':tree.tag,'elements':dict(Counter(n.tag for n in tree.iter())),'semanticCompatibility':'unverified'}

def stage_xml(source: Path, output: Path, url: str, rights: str) -> dict:
    raw=source.read_bytes();info=inspect_xml(raw)
    if not rights.strip() or not url.startswith(('https://','http://')):
        raise ValueError('Source URL and rights note are required')
    output.mkdir(parents=True,exist_ok=True);target=output/source.name
    if target.exists() and target.read_bytes()!=raw:
        raise ValueError('Refusing to overwrite an existing different witness')
    target.write_bytes(raw)
    manifest={**info,'file':source.name,'sourceURL':url,'rightsNote':rights,'operation':'preserved raw bytes; no semantic conversion','retrieved':datetime.now(timezone.utc).isoformat()}
    (output/(source.name+'.manifest.json')).write_text(dump(manifest),encoding='utf-8')
    return manifest

def collate(old: str, new: str) -> dict:
    plain=lambda text: ''.join(TextIndex(text).text) if '<p' in text else text
    a,b=plain(old),plain(new)
    normalize=lambda text: ''.join(c for c in text if c not in PUNCTUATION and not c.isspace())
    kind='unchanged' if a==b else 'punctuation-or-whitespace' if normalize(a)==normalize(b) else 'wording'
    return {'kind':kind,'requiresInterpretationReview':kind!='unchanged','diff':''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='base',tofile='incoming'))}

def merge_candidate(base: Path, ours: Path, theirs: Path, output: Path) -> dict:
    if output.resolve() in {p.resolve() for p in (base,ours,theirs)}:
        raise ValueError('Merge output must not overwrite an input')
    result=subprocess.run(['git','merge-file','--diff3','--stdout',str(ours),str(base),str(theirs)],capture_output=True)
    if result.returncode<0 or result.returncode>=128:
        raise ValueError(result.stderr.decode('utf-8','replace'))
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(result.stdout)
    return {'candidate':str(output),'conflicts':result.returncode,'applied':False,'reviewRequired':True}

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('validate')
    p=sub.add_parser('context');p.add_argument('passage')
    p=sub.add_parser('build-db');p.add_argument('--output',type=Path,default=ROOT/'build/renwen.sqlite')
    p=sub.add_parser('validate-proposals');p.add_argument('file',type=Path)
    p=sub.add_parser('apply-proposals');p.add_argument('file',type=Path);p.add_argument('--reviewer',required=True)
    p=sub.add_parser('inspect-xml');p.add_argument('file',type=Path)
    p=sub.add_parser('ctext-stage');p.add_argument('file',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--source-url',required=True);p.add_argument('--rights-note',required=True)
    p=sub.add_parser('collate');p.add_argument('base',type=Path);p.add_argument('incoming',type=Path)
    p=sub.add_parser('merge');p.add_argument('base',type=Path);p.add_argument('ours',type=Path);p.add_argument('incoming',type=Path);p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.command=='validate': result=validate()
        elif args.command=='context': result=context(args.passage)
        elif args.command=='build-db': result=build_db(args.output)
        elif args.command=='validate-proposals': validate();result={'valid':len(proposals(args.file,load_catalog()))}
        elif args.command=='apply-proposals': result=apply_proposals(args.file,args.reviewer)
        elif args.command=='inspect-xml': result=inspect_xml(args.file.read_bytes())
        elif args.command=='ctext-stage': result=stage_xml(args.file,args.output,args.source_url,args.rights_note)
        elif args.command=='collate': result=collate(args.base.read_text(encoding='utf-8'),args.incoming.read_text(encoding='utf-8'))
        elif args.command=='merge': result=merge_candidate(args.base,args.ours,args.incoming,args.output)
        print(dump(result),end='')
    except (ValueError,KeyError,TypeError,OSError,ET.ParseError,sqlite3.Error) as error:
        print(f'Error: {error}',file=sys.stderr);return 1
    return 0
if __name__=='__main__': sys.exit(main())
