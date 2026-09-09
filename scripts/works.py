#!/usr/bin/env python3
"""Validate named works and index them into the derived corpus database."""
from __future__ import annotations
import argparse, json, re, sqlite3
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]

def load_works(root:Path=ROOT)->list[dict]:
    folder=root/'data/works';index=json.loads((folder/'index.json').read_text())
    if index.get('schemaVersion')!=1 or not isinstance(index.get('works'),list):raise ValueError('Invalid work index')
    catalog=json.loads((root/'data/catalog.json').read_text());entities={e['id']:e for e in catalog['entities']}
    mentions={m['id']:m for m in catalog['mentions']};result=[];seen=set()
    for filename in index['works']:
        if not isinstance(filename,str) or not re.fullmatch(r'work-[a-z0-9-]+\.json',filename) or filename in seen:raise ValueError('Invalid or duplicate work filename')
        seen.add(filename);p=json.loads((folder/filename).read_text())
        if p.get('schemaVersion')!=1 or p.get('type')!='work' or filename!=p.get('id','')+'.json' or not p.get('title'):raise ValueError('Invalid work identity')
        if entities.get(p['id'],{}).get('type')!='work':raise ValueError('Missing work entity')
        if p.get('reviewStatus') not in {'agent-proposed','reviewed','disputed'}:raise ValueError('Invalid work review status')
        if p['reviewStatus']=='reviewed' and not p.get('reviewedBy'):raise ValueError('Actual reviewer required')
        if not p.get('sources') or not p.get('mentions'):raise ValueError('Work evidence required')
        for source in p['sources'].values():
            u=urlparse(source.get('url',''))
            if u.scheme not in {'http','https'} or not u.netloc:raise ValueError('Unsafe work evidence URL')
        for creator in p.get('creators',[]):
            if entities.get(creator.get('person'),{}).get('type')!='person' or not creator.get('role'):raise ValueError('Invalid work contributor')
        for key in ['translationOf','commentsOn','possibleSameAs']:
            if p.get(key) and (entities.get(p[key],{}).get('type')!='work' or p[key]==p['id']):raise ValueError('Invalid related work')
        for m in p['mentions']:
            actual=mentions.get(m.get('mention'))
            if not actual or actual['entity']!=p['id'] or actual['passage']!=m.get('passage') or actual['witness']!=m.get('witness'):raise ValueError('Stale work occurrence; rebuild the work backlinks after reviewing an annotation')
        result.append(p)
    if {e['id'] for e in entities.values() if e['type']=='work'}!={p['id'] for p in result}:raise ValueError('A named work lacks its profile')
    return result

def index_db(path:Path,root:Path=ROOT)->dict:
    records=load_works(root)
    if not path.is_file():raise ValueError('Build the corpus database first')
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('CREATE TABLE IF NOT EXISTS work_profiles(id TEXT PRIMARY KEY REFERENCES entities(id), title TEXT NOT NULL, kind TEXT, metadata TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS work_contributors(work_id TEXT REFERENCES work_profiles(id),person_id TEXT REFERENCES entities(id),role TEXT NOT NULL)')
        db.execute('DELETE FROM work_contributors');db.execute('DELETE FROM work_profiles')
        for w in records:
            db.execute('INSERT INTO work_profiles VALUES(?,?,?,?)',(w['id'],w['title'],w.get('kind'),json.dumps(w,ensure_ascii=False)))
            for c in w.get('creators',[]):db.execute('INSERT INTO work_contributors VALUES(?,?,?)',(w['id'],c['person'],c['role']))
        if db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Invalid work foreign key')
    return {'works':len(records),'database':str(path),'derived':True}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['validate','index-db']);p.add_argument('--database',type=Path,default=ROOT/'build/renwen.sqlite');a=p.parse_args()
    try:print(json.dumps(index_db(a.database) if a.command=='index-db' else {'works':len(load_works()),'valid':True}))
    except (ValueError,KeyError,TypeError,OSError,sqlite3.Error) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
