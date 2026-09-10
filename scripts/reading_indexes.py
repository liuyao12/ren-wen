"""Build compact, derived reading indexes; individual JSON files stay authoritative."""
from __future__ import annotations
import argparse,copy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def encode(obj):return json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n'
def build(root=ROOT):
    counts={}
    for folder,key in [('people','profiles'),('works','works')]:
        base=root/'data'/folder;index=json.loads((base/'index.json').read_text());records=[]
        for file in index[key]:
            p=json.loads((base/file).read_text())
            if folder=='people':
                out={k:copy.deepcopy(p[k]) for k in ['schemaVersion','id','collection','reviewStatus','name','life','externalIds','accounts']}
                out['name'].pop('registration',None)
                keys={a.get('source') for a in p['accounts']} | {p['name'].get('source')} | {x.get('source') for x in p['life'].get('westernYears',[])} | {x.get('source') for x in p['life'].get('westernDates',[])} | {(p['life'].get(e) or {}).get('source') for e in ['birth','death']}
                out['sources']={key:{'title':p['sources'][key]['title'],'url':p['sources'][key]['url']} for key in keys if key in p['sources']}
            else:out={k:copy.deepcopy(p.get(k,[] if k in ['attestedTitles','creators'] else '')) for k in ['schemaVersion','id','type','title','attestedTitles','kind','creators','reviewStatus']}
            out['summaryOnly']=True;records.append(out)
        bundle={'schemaVersion':1,'derived':True,'records':records}
        (base/'bundle.json').write_text(encode(bundle),encoding='utf-8')
        index['bundle']='bundle.json';(base/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');counts[folder]=len(records)
    c=json.loads((root/'data/catalog.json').read_text());collection=json.loads((root/'data/collections/eccp.json').read_text())
    ps={p['id']:p for p in json.loads((root/'data/people/bundle.json').read_text())['records']}
    ss={s['id']:s for s in c['sources']};rows=[]
    for entry in collection['entries']:
        e=copy.deepcopy(entry);p=ps.get(e['person']);n=p['name'] if p else {}
        qualifier=(n.get('bracket') or {}).get('label','')
        bare=(n.get('surname') or '')+n.get('given','')
        e.update(name=bare,qualifier=qualifier,alias=(n.get('parenthetical') or {}).get('value',''),years=[x['value'] for x in (p or {}).get('life',{}).get('westernYears',[])],qsg=bool(p and any(a.get('readerWitness','').startswith('qsg') for a in p['accounts'])))
        rows.append(e)
    (root/'data/collections/eccp-reading-index.json').write_text(encode({'schemaVersion':1,'derived':True,'counts':collection['counts'],'entries':rows}),encoding='utf-8')
    return counts
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();print(json.dumps(build(a.root)))
