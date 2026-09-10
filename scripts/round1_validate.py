"""Audit complete ECCP inventory, source wording, local destinations and derived indexes."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from .round1_import import reading_blocks,compact,toc_rows
from .renwen import TextIndex
from .reading_indexes import encode
ROOT=Path(__file__).resolve().parents[1]
def validate(root=ROOT):
    c=json.loads((root/'data/catalog.json').read_text());sources={s['id']:s for s in c['sources']}
    collection=json.loads((root/'data/collections/eccp.json').read_text());inventory=json.loads((root/'data/imports/round1/inventory.json').read_text())
    expected={x['pageid'] for x in inventory['eccp']};actual={x['pageid'] for x in collection['entries']}
    assert expected==actual,'ECCP source inventory incomplete'
    assert len(actual)==len(collection['entries']),'Duplicate ECCP inventory row'
    source_text={};source_paragraphs={}
    for entry in collection['entries']:
        s=sources[entry['source']];raw=(root/s['rawResponse']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==s['rawSha256'],s['id']
        _,whole=reading_blocks(json.loads(raw)['parse']['text']['*'])
        text=TextIndex((root/s['upstream']).read_text());source_paragraphs[s['id']]=text.passages
        assert compact(''.join(text.passages.values()))==whole, f'Missing source text: {s["id"]}'
        assert s['complete'],s['id']
    for file in (root/'data/people').glob('person-*.json'):
        p=json.loads(file.read_text());n=p['name']
        if n.get('bracket'):
            assert n['bracket']['kind'] in {'county','clan'}
            assert n['bracket']['source'] in p['sources']
        for account in p['accounts']:
            wid=account.get('readerWitness')
            if not wid:continue
            assert wid in sources,(p['id'],wid)
            pid=account.get('passage')
            if pid and pid.startswith(wid+'-'):
                if wid not in source_paragraphs:source_paragraphs[wid]=TextIndex((root/sources[wid]['text']).read_text()).passages
                assert pid in source_paragraphs[wid],(p['id'],pid)
    concordance=json.loads((root/'data/collections/qsg-concordance.json').read_text())
    for match in concordance['matches']:
        wid=match['witness'];s=sources[wid]
        assert s['work']=='work-qingshigao' and s['complete']
        if wid not in source_paragraphs:source_paragraphs[wid]=TextIndex((root/s['text']).read_text()).passages
        assert source_paragraphs[wid][match['passage']].strip().startswith(match['opening'])
        assert match['status']=='proposed','Do not turn matching into a human review'
    for directory,key in [('people','profiles'),('works','works')]:
        base=root/'data'/directory;index=json.loads((base/'index.json').read_text());bundle=json.loads((base/'bundle.json').read_text())
        assert bundle['derived'] is True
        assert [r['id']+'.json' for r in bundle['records']]==index[key]
        for row in bundle['records']:
            p=json.loads((base/(row['id']+'.json')).read_text())
            if directory=='people':assert row['name'].get('bracket')==p['name'].get('bracket') and row['externalIds']==p['externalIds']
            else:assert row['title']==p['title']
    return {**collection['counts'],'inventoryComplete':True,'fullTextChecked':True,'localAccountsChecked':True,'bundlesChecked':True}
if __name__=='__main__':print(json.dumps(validate(),ensure_ascii=False,indent=2))
