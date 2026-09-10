"""Conservative corpus-wide place pass, with separately reviewable lexical candidates.

Source wording/formatting and existing occurrence IDs are byte-preserved. No
coordinates, administrative succession or travel are inferred from a mention.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from html import unescape
from pathlib import Path
import hashlib, json, re
from .renwen import TextIndex
from .reading_indexes import build
ROOT=Path(__file__).resolve().parents[1]
VERSION='places-2026-09-10-v1'
# Editorial spelling equivalences for geographic expressions, not timeless polygons.
PROVINCES=[('anhwei','安徽','Anhwei|Anhui'),('chekiang','浙江','Chekiang|Zhejiang'),
 ('chihli','直隸','Chihli|Chih-li'),('fukien','福建','Fukien|Fujian'),
 ('honan','河南','Honan|Henan'),('hupeh','湖北','Hupeh|Hubei'),('hunan','湖南','Hunan'),
 ('kansu','甘肅','Kansu|Gansu'),('kiangsi','江西','Kiangsi|Jiangxi'),('kiangsu','江蘇','Kiangsu|Jiangsu'),
 ('kwangtung','廣東','Kwangtung|Guangdong'),('kwangsi','廣西','Kwangsi|Guangxi'),
 ('kweichow','貴州','Kweichow|Guizhou'),('shansi','山西','Shansi|Shan-hsi'),
 ('shensi','陝西','Shensi|Shaanxi'),('shantung','山東','Shantung|Shandong'),
 ('szechwan','四川','Szechwan|Szechuan|Sichuan'),('yunnan','雲南','Yunnan')]
# Already present, sourced locations; no new coordinates introduced here.
EXISTING={'place-xiangxiang':['Hsiang-hsiang','湘鄉','湘鄉縣'],
 'place-peking':['Peking'], 'place-shanghai':['Shanghai','上海'],
 'place-paris':['Paris','巴黎'], 'place-london':['London','倫敦'],
 'place-petersburg':['St. Petersburg','St Petersburg','聖彼得堡']}
TOKEN=re.compile(r'<[^>]*>|&(?:#\d+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]+);|[^<&]+|[<&]')
HAN=r'[\u3400-\u9fff]'
def norm(s):return s.casefold().replace('’',"'").replace('‘',"'").replace('‑','-')
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def pattern(term):
    value=re.escape(term).replace("'","['’‘]")
    return re.compile(r"(?<![\w'’-])"+value+r"(?![\w'’-])" if re.search('[A-Za-z]',term) else value,re.I if re.search('[A-Za-z]',term) else 0)

def leaf_ranges(markup):
    """Return raw/plain coordinates and protected state, without reserializing HTML."""
    stack=[];offset=0;parts=[];runs=[]
    for token in TOKEN.finditer(markup):
        raw=token[0]
        if raw.startswith('<') and raw.endswith('>'):
            closing=re.match(r'</([\w-]+)',raw)
            opening=re.match(r'<([\w-]+)',raw)
            if closing:
                for i in range(len(stack)-1,-1,-1):
                    if stack[i][0]==closing[1]:del stack[i:];break
            elif opening and not raw.endswith('/>') and opening[1] not in {'br','wbr','hr','img','input'}:
                stack.append((opening[1], opening[1] in {'a','i','em'} or 'data-entity=' in raw))
            continue
        decoded=unescape(raw);protected=any(x[1] for x in stack)
        runs.append((offset,offset+len(decoded),token.start(),token.end(),decoded,protected,raw==decoded))
        parts.append(decoded);offset+=len(decoded)
    return ''.join(parts),runs

def eligible_hits(markup,rules,language):
    plain,runs=leaf_ranges(markup);hits=[]
    titles=[m.span() for m in re.finditer(r'《[^》]*》|〈[^〉]*〉',plain)]
    for term,ident,scope in rules:
        for match in pattern(term).finditer(plain):
            a,b=match.span()
            if any(a<y and b>x for x,y in titles):continue
            covering=[r for r in runs if a<r[1] and b>r[0]]
            if not covering or any(r[5] for r in covering):continue
            if any(not r[6] for r in covering):continue # no partial HTML entity rewrites
            # Do not cross a source-formatting boundary during this conservative pass.
            if len(covering)!=1:continue
            before=plain[max(0,a-65):a]
            if scope=='local-native' and not re.search(r'\b(?:of|at|in|to|from|near|through|around|outside|entered|reached|left)\s+$',before,re.I):continue
            # 直隸 also describes administrative status; require an explicit place usage.
            if term=='直隸' and language!='en' and not re.search(r'(?:於|至|自|入|出|往|赴|改|調|籍|隸|督|撫)$',before) and not re.match(r'(?:省|總督|巡撫|布政使|按察使|人)',plain[b:]):continue
            run=covering[0];raw_a=run[2]+a-run[0];raw_b=run[2]+b-run[0]
            hits.append((a,b,raw_a,raw_b,ident,scope))
    hits.sort(key=lambda x:(x[0],-(x[1]-x[0]),x[4]))
    selected=[];end=-1
    for hit in hits:
        if hit[0]<end:continue
        # Two possible identities for the same span remain a review problem.
        if len({h[4] for h in hits if h[:2]==hit[:2]})>1:continue
        selected.append(hit);end=hit[1]
    return plain,selected

def rebase_text_occurrences(data, changes):
    """Rebase revision pins only after exact, unchanged text/range verification.

    changes maps witness IDs to (old_hash, new_hash, old_passages, new_passages).
    It is not a general fuzzy anchor relocation or a transcription-edit merge.
    """
    pending=[]
    for occurrence in data['occurrences']:
        change=changes.get(occurrence['witness'])
        if change is None: continue
        old_hash,new_hash,old_passages,new_passages=change
        if old_passages!=new_passages:
            raise ValueError('Source wording changed; text anchors require review')
        if occurrence.get('sourceSha256')!=old_hash:
            raise ValueError('Pre-existing stale text occurrence; refusing to rebase')
        for selector in occurrence['selectors']:
            passage=old_passages.get(selector['passage'])
            a,b=selector['start'],selector['end']
            if passage is None or not 0<=a<b<=len(passage) or passage[a:b]!=selector['exact']:
                raise ValueError('Text occurrence selector is not exact')
        pending.append((occurrence,new_hash))
    for occurrence,new_hash in pending: occurrence['sourceSha256']=new_hash
    return [occurrence['id'] for occurrence,_ in pending]

def run(root=ROOT):
    reportpath=root/'data/editorial/place-pass.json'
    if reportpath.exists():return json.loads(reportpath.read_text())
    c=json.loads((root/'data/catalog.json').read_text());es={e['id']:e for e in c['entities']}
    ss={s['id']:s for s in c['sources']};collection=json.loads((root/'data/collections/eccp.json').read_text())
    kinds={e['source']:e['kind'] for e in collection['entries']}
    sources=[s for s in c['sources'] if kinds.get(s['id'])!='cross-reference']
    profiles={}
    global_rules=[];native_rules=defaultdict(list);definitions={};evidence=defaultdict(list);native_candidates=[]
    for slug,han,spellings in PROVINCES:
        ident='place-region-'+slug
        definitions[ident]={'id':ident,'label':han,'display':spellings.split('|')[0],'kind':'geographic-expression','spellingForms':[han]+spellings.split('|'),'resolution':'Place expression identified; historical jurisdiction, boundaries and temporal identity require separate review.'}
        global_rules += [(t,ident,'province-expression') for t in definitions[ident]['spellingForms']]
    for ident,terms in EXISTING.items():
        if ident not in es:continue
        definitions[ident]={'id':ident,'label':es[ident]['label'],'display':es[ident]['display'],'kind':'existing-reference-place','spellingForms':terms,'resolution':'Retains the existing source-limited place record. A reference point is not a historical boundary or evidence of travel.'}
        global_rules += [(t,ident,'existing-place') for t in terms]
    provinces={norm(t):(slug,han) for slug,han,spellings in PROVINCES for t in spellings.split('|')}
    # Native place clauses provide local antecedents, not unrestricted global aliases.
    native=re.compile(r"\bnative of\s+([A-Z][A-Za-zÀ-ž'’‘-]*(?:\s+[A-Z][A-Za-zÀ-ž'’‘-]*){0,2})(?:\s*\(([^)]{1,50})\))?,\s*([A-Z][A-Za-z-]+)\b")
    for s in sources:
        if s.get('language')!='en':continue
        ps=TextIndex((root/s['text']).read_text()).passages
        for pid,plain in ps.items():
            for m in native.finditer(plain):
                name,parent=m[1],provinces.get(norm(m[3]))
                if not parent:continue
                existing=next((i for i,terms in EXISTING.items() if i in es and any(norm(t)==norm(name) for t in terms)),None)
                ident=existing or 'place-native-'+digest(norm(name)+'|'+parent[0])[:12]
                if ident not in definitions:
                    definitions[ident]={'id':ident,'label':name,'display':name,'kind':'source-native-place','spellingForms':[name], 'provinceExpression':parent[1], 'resolution':'Native-place expression with province context. Chinese equivalence, county/prefecture identity and coordinates are not inferred.'}
                native_rules[s['id']].append((name,ident,'local-native'))
                native_candidates.append({'witness':s['id'],'passage':pid,'quote':m[0],'place':ident,'status':'source-limited-proposal','sourceUrl':s['revisionUrl']})
    bysource=defaultdict(int);added=[];candidates=[];unchanged=0;changed=0; revisions={}
    all_existing_ids={m['id'] for m in c['mentions']}
    for s in sources:
        text=(root/s['text']).read_text();original=text;paragraphs=list(re.finditer(r'<p\s+id="([^"]+)"[^>]*>.*?</p>',text,re.S));replacements=[]
        rules=list(dict.fromkeys(global_rules+native_rules[s['id']]))
        for pm in paragraphs:
            pid=pm[1];markup=pm[0];plain,hits=eligible_hits(markup,rules,s['language']);edits=[]
            existing_ids=all_existing_ids
            for a,b,ra,rb,ident,scope in hits:
                mid=pid+'-place-'+digest(f'{a}:{b}:{ident}')[:12]
                assert mid not in existing_ids
                quote=plain[a:b]
                assert unescape(markup[ra:rb])==quote
                edits.append((ra,rb,f'<span id="{mid}" data-entity="{ident}">'+markup[ra:rb]+'</span>'))
                mention={'id':mid,'witness':s['id'],'passage':pid,'entity':ident,'quote':quote,'status':'proposed','origin':VERSION,'note':'Geographic expression, not a travel claim. '+scope+'; identification is a conservative first-pass proposal.'}
                added.append(mention);evidence[ident].append({'witness':s['id'],'passage':pid,'mention':mid,'quote':quote,'sourceUrl':s['revisionUrl']});bysource[s['id']]+=1
            # Lexical candidates do not become entity links or coordinates automatically.
            if s['language']!='en':
                protected_runs=leaf_ranges(markup)[1]
                for m in re.finditer(r'(?:^|[，。；：、\s於至居赴駐往])('+HAN+r'{1,4}(?:縣|府|州|廳|省|山|河|湖|關))',plain):
                    a,b=m.span(1)
                    if any(a<y and b>x for x,y,*_ in hits):continue
                    if any(a<r[1] and b>r[0] and r[5] for r in protected_runs):continue
                    candidates.append({'witness':s['id'],'passage':pid,'quote':m[1],'start':a,'end':b,'context':plain[max(0,a-35):b+35],'status':'needs-review','reason':'geographic-suffix-only; segmentation and identity not confirmed'})
            for ra,rb,replacement in reversed(edits):markup=markup[:ra]+replacement+markup[rb:]
            if edits:replacements.append((pm.start(),pm.end(),markup))
        for a,b,new in reversed(replacements):text=text[:a]+new+text[b:]
        old_passages=TextIndex(original).passages;new_passages=TextIndex(text).passages
        assert new_passages==old_passages,s['id']
        if replacements: revisions[s['id']]=(s['sha256'],digest(text),old_passages,new_passages)
        if replacements:(root/s['text']).write_text(text);s['sha256']=digest(text);changed+=1
        else:unchanged+=1
        s.setdefault('annotationCoverage',{})['places']='rule-scanned; source-limited proposals; contextual and geographic review pending'
    unit_path=root/'data/text-units.json'
    units=json.loads(unit_path.read_text())
    rebased=rebase_text_occurrences(units,revisions)
    c['mentions'].extend(added)
    records=[]
    for ident,d in definitions.items():
        ms=evidence[ident]
        if not ms:continue
        records.append({**d,'status':'proposed','evidence':ms,'nativeClauses':[x for x in native_candidates if x['place']==ident]})
        if ident not in es:
            e={'id':ident,'type':'place','label':d['label'],'display':d['display'],'aliases':d['spellingForms'],'sources':sorted({m['witness'] for m in ms}),'point':None,'note':d['resolution']}
            c['entities'].append(e);es[ident]=e
    represented={p['id'] for p in records}
    for e in c['entities']:
        if e['type']!='place' or e['id'] in represented:continue
        ms=[{'witness':m['witness'],'passage':m['passage'],'mention':m['id'],'quote':m['quote'],'sourceUrl':ss[m['witness']]['revisionUrl']} for m in c['mentions'] if m['entity']==e['id']]
        records.append({'id':e['id'],'label':e['label'],'display':e.get('display',e['label']), 'kind':'existing-reference-place','spellingForms':e.get('aliases',[]), 'resolution':e.get('note','Existing reference place; no new geographical assertion.'),'status':'proposed','evidence':ms,'nativeClauses':[]})
    report={'version':VERSION,'textOccurrencePinsRebased':rebased,'anchorRebaseReason':'Markup only; paragraph text and every selector verified unchanged before revision update.','sourcesScanned':len(sources),'eccpBiographiesScanned':sum(kinds.get(s['id'])=='biography' for s in sources),'qsgSourcesScanned':sum(s.get('work') in {'work-qingshigao','work-qsg'} for s in sources),'sourcesWithNewMentions':changed,'newPlaceMentions':len(added),'placeRecords':len(records),'nativeClauses':len(native_candidates),'unresolvedLexicalCandidates':len(candidates),'sourceWordsChanged':0,'sources':dict(bysource),'status':'corpus-wide rule pass, not exhaustive human review','limits':'No raw CHGIS gazetteer is imported. New place expressions have no coordinates. Repeated native-place forms are scoped to their source and prepositional context. Existing person/work spans, italics and Chinese book-title brackets are protected.'}
    collection['counts']['mentions']=len(c['mentions'])
    write(unit_path,units)
    write(root/'data/catalog.json',c);write(root/'data/collections/eccp.json',collection)
    write(root/'data/places.json',{'schemaVersion':1,'records':records})
    write(root/'data/editorial/place-candidates.json',{'schemaVersion':1,'status':'needs-review','candidates':candidates})
    write(reportpath,report);build(root);return report
if __name__=='__main__':
    result=run();print(json.dumps({k:v for k,v in result.items() if k!='sources'},ensure_ascii=False,indent=2))
