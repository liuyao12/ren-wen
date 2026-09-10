"""Validate dated names, title periods and paragraph anchors; build derived SQL indexes."""
from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path
from .renwen import TextIndex
ROOT=Path(__file__).resolve().parents[1]
def validate(root:Path=ROOT):
    data=json.loads((root/'data/name-history.json').read_text(encoding='utf-8'))
    assert data.get('schemaVersion')==1,'Unsupported name history'
    catalog=json.loads((root/'data/catalog.json').read_text(encoding='utf-8'))
    sources={s['id']:s for s in catalog['sources']};texts={}
    def evidence(e):
        w=e['witness'];assert w in sources,'Unknown evidence witness'
        if w not in texts:texts[w]=TextIndex((root/sources[w]['text']).read_text(encoding='utf-8')).passages
        assert e.get('passage') in texts[w],'Unknown evidence passage'
        assert isinstance(e.get('quote'),str) and e['quote'] and e['quote'] in texts[w][e['passage']],'Evidence quotation changed'
    total=0
    for pid,record in data.get('people',{}).items():
        assert (root/'data/people'/f'{pid}.json').is_file(),'Unknown profile'
        ids=set()
        for kind in ['names','titles']:
            periods=record.get(kind,[])
            assert sum(bool(p.get('defaultDisplay')) for p in periods)<=1,'Conflicting default names'
            for p in periods:
                assert p['id'] not in ids,'Duplicate period id';ids.add(p['id']);total+=1
                assert p['kind'] in {'personal-name','office','noble','regnal','temple','posthumous'}
                for bound in ['from','to']:
                    assert p.get(bound) is None or (type(p[bound]) is int and 1<=p[bound]<=9999),'Invalid boundary'
                assert p['from'] is None or p['to'] is None or p['to']>p['from'],'Reversed period'
                assert p['status'] in {'proposed','reviewed','rejected','superseded'},'Invalid review status'
                assert p.get('evidence'),'Unsourced name period'
                if kind=='titles':assert p.get('label') and p.get('shortLabel'),'Missing title labels'
                else:assert p.get('given') or p.get('label'),'Missing personal name'
                for e in p['evidence']:evidence(e)
        for aliases in record.get('aliases',{}).values():
            for alias in aliases:
                assert alias.get('value') and alias.get('evidence'),'Unsourced alias'
                for e in alias['evidence']:evidence(e)
        for attestation in record.get('attestations',[]):evidence(attestation)
    anchors=set()
    for a in data.get('paragraphAnchors',[]):
        key=(a['witness'],a['passage']);assert key not in anchors,'Conflicting paragraph anchors';anchors.add(key)
        assert type(a.get('year')) is int and 1<=a['year']<=9999
        assert a.get('status') in {'proposed','reviewed'} and a.get('basis')
        evidence(a)
    for work,date in data.get('workDates',{}).items():
        assert work in {s['work'] for s in sources.values()}
        assert date.get('kind') and date.get('basis') and date.get('label'),'Missing source-date provenance'
    return {'peopleWithDatedRecords':len(data.get('people',{})),'periods':total,'paragraphAnchors':len(anchors),'valid':True}

def index_db(path:Path,root:Path=ROOT):
    result=validate(root);assert path.is_file(),'Build corpus DB first'
    data=json.loads((root/'data/name-history.json').read_text(encoding='utf-8'))
    db=sqlite3.connect(path)
    try:
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS person_name_periods(person_id TEXT NOT NULL, period_id TEXT NOT NULL, kind TEXT NOT NULL, start_year INTEGER, end_year_exclusive INTEGER, metadata TEXT NOT NULL, PRIMARY KEY(person_id,period_id))')
            db.execute('DELETE FROM person_name_periods')
            for pid,r in data.get('people',{}).items():
                for p in r.get('names',[])+r.get('titles',[]):db.execute('INSERT INTO person_name_periods VALUES(?,?,?,?,?,?)',(pid,p['id'],p['kind'],p['from'],p['to'],json.dumps(p,ensure_ascii=False)))
            db.execute('CREATE TABLE IF NOT EXISTS source_date_assertions(work_id TEXT PRIMARY KEY, metadata TEXT NOT NULL)')
            db.execute('DELETE FROM source_date_assertions')
            for work,date in data.get('workDates',{}).items():db.execute('INSERT INTO source_date_assertions VALUES(?,?)',(work,json.dumps(date,ensure_ascii=False)))
            db.execute('DROP VIEW IF EXISTS person_source_names')
            db.execute('''CREATE VIEW person_source_names AS
              SELECT m.entity AS person_id, m.witness, m.passage, m.id AS mention_id,
              json_extract(m.metadata, '$.quote') AS source_form, d.metadata AS source_date
              FROM mentions m JOIN entities e ON e.id=m.entity JOIN sources s ON s.id=m.witness
              LEFT JOIN source_date_assertions d ON d.work_id=s.work WHERE e.type='person' ''')
    finally:db.close()
    return {**result,'derived':True}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['validate','index-db']);parser.add_argument('--database',type=Path,default=ROOT/'build/renwen.sqlite');a=parser.parse_args()
    print(json.dumps(validate() if a.command=='validate' else index_db(a.database),ensure_ascii=False,indent=2))
