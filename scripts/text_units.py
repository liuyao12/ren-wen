"""Validate layered text identities and versioned occurrences; build derived SQL tables."""
from pathlib import Path
import argparse,hashlib,json,re,sqlite3
from .renwen import TextIndex
ROOT=Path(__file__).resolve().parents[1]

def validate_units(data,catalog,passages):
    if data.get('schemaVersion')!=1:raise ValueError('Unsupported text-unit schema')
    units={u['id']:u for u in data['units']};occs={o['id']:o for o in data['occurrences']};sources={s['id']:s for s in catalog['sources']}
    if len(units)!=len(data['units']) or len(occs)!=len(data['occurrences']):raise ValueError('Duplicate text identity or occurrence ID')
    for u in units.values():
        if not re.fullmatch('text-[a-z0-9-]+',u['id']) or not u.get('title') or not u.get('kind'):raise ValueError('Invalid text unit')
        if u.get('parentUnit') and u['parentUnit'] not in units:raise ValueError('Unknown parent unit')
        if u.get('reviewStatus')=='reviewed' and not u.get('reviewedBy'):raise ValueError('Actual reviewer required')
    for o in occs.values():
        if not re.fullmatch('occ-[a-z0-9-]+',o['id']) or o.get('unit') not in units or o.get('witness') not in sources:raise ValueError('Invalid occurrence identity')
        if o.get('sourceSha256')!=sources[o['witness']]['sha256']:raise ValueError('Stale text occurrence; review its anchor after source changes')
        if o.get('role') not in ['complete-reading','quotation','section','excerpt'] or o.get('readingType') not in ['source-reading','quoted-reading','variant-reading','translation']:raise ValueError('Invalid textual relationship or reading type')
        if not o.get('selectors'):raise ValueError('An occurrence needs source ranges')
        for a in o['selectors']:
            text=passages.get((o['witness'],a.get('passage')))
            if text is None or type(a.get('start'))!=int or type(a.get('end'))!=int or not 0<=a['start']<a['end']<=len(text):raise ValueError('Invalid code-point range')
            if text[a['start']:a['end']]!=a.get('exact'):raise ValueError('Occurrence quote differs from its source range')
        if o.get('container'):
            parent=occs.get(o['container'])
            if not parent or parent['witness']!=o['witness']:raise ValueError('Container must be a reading in the same witness')
            for a in o['selectors']:
                if not any(b['passage']==a['passage'] and b['start']<=a['start'] and b['end']>=a['end'] for b in parent['selectors']):raise ValueError('Child range lies outside its containing reading')
    def check_cycles(rows,key):
        for ident in rows:
            seen=set();cur=ident
            while cur:
                if cur in seen:raise ValueError('Cyclic text hierarchy')
                seen.add(cur);cur=rows[cur].get(key)
    check_cycles(units,'parentUnit');check_cycles(occs,'container')
    for r in data.get('relations',[]):
        if r.get('from') not in occs or r.get('to') not in occs or r['from']==r['to']:raise ValueError('Invalid reading correspondence')
        if r.get('type') not in ['quotes','paraphrases','translates','parallel-reading','derived-from'] or not r.get('evidence'):raise ValueError('Textual correspondence requires explicit type and evidence')
    return data

def load_units(root=ROOT):
    c=json.loads((root/'data/catalog.json').read_text());passages={}
    for s in c['sources']:
        raw=(root/s['text']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=s['sha256']:raise ValueError('Unrecorded source change')
        passages.update({(s['id'],pid):t for pid,t in TextIndex(raw.decode()).passages.items()})
    return validate_units(json.loads((root/'data/text-units.json').read_text()),c,passages)

def index_db(path,root=ROOT):
    d=load_units(root)
    if not path.exists():raise ValueError('Build corpus database first')
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript('CREATE TABLE IF NOT EXISTS text_units(id TEXT PRIMARY KEY,title TEXT NOT NULL,kind TEXT,metadata TEXT); CREATE TABLE IF NOT EXISTS text_occurrences(id TEXT PRIMARY KEY,unit_id TEXT REFERENCES text_units(id),witness TEXT REFERENCES sources(id),container_id TEXT,metadata TEXT); CREATE TABLE IF NOT EXISTS text_correspondences(id TEXT PRIMARY KEY,source_occurrence TEXT REFERENCES text_occurrences(id),target_occurrence TEXT REFERENCES text_occurrences(id),type TEXT,metadata TEXT);')
        db.execute('DELETE FROM text_correspondences');db.execute('DELETE FROM text_occurrences');db.execute('DELETE FROM text_units')
        for u in d['units']:db.execute('INSERT INTO text_units VALUES(?,?,?,?)',(u['id'],u['title'],u['kind'],json.dumps(u,ensure_ascii=False)))
        for o in d['occurrences']:db.execute('INSERT INTO text_occurrences VALUES(?,?,?,?,?)',(o['id'],o['unit'],o['witness'],o.get('container'),json.dumps(o,ensure_ascii=False)))
        for r in d['relations']:db.execute('INSERT INTO text_correspondences VALUES(?,?,?,?,?)',(r['id'],r['from'],r['to'],r['type'],json.dumps(r,ensure_ascii=False)))
        if db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Invalid text foreign key')
    return {'units':len(d['units']),'occurrences':len(d['occurrences']),'derived':True}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['validate','index-db']);p.add_argument('--database',type=Path,default=ROOT/'build/renwen.sqlite');a=p.parse_args()
    print(json.dumps(index_db(a.database) if a.command=='index-db' else {'units':len(load_units()['units']),'valid':True}))
