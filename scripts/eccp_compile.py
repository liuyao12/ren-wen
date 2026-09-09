"""Build the explicit, agent-proposed ECCP batch; no network calls."""
from pathlib import Path
import json, re, hashlib, copy
from urllib.parse import quote
from .eccp_batch import source_paragraphs, split_paragraphs, fragment, annotate

PREFIX="Eminent Chinese of the Ch'ing Period/"
url=lambda name:'https://en.wikisource.org/wiki/'+quote((PREFIX+name).replace(' ','_'),safe='/')
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

# These are Chinese renderings of the native-place strings in the preserved ECCP openings.
PLACES={
 'person-qi-junzao':'山西壽陽','person-zhang-zhidong':'直隸南皮','person-zhang-peilun':'直隸豐潤',
 'person-jiang-zhongyuan':'湖南新寧','person-feng-zicai':'廣東欽州','person-xu-jiyu':'山西五臺',
 'person-hong-rengan':'廣東花縣','person-li-hongzhang':'安徽合肥','person-liu-ruifen':'安徽貴池',
 'person-liu-mingchuan':'安徽合肥','person-luo-bingzhang':'廣東花縣','person-peng-yulin':'湖南衡陽',
 'person-ding-richang':'廣東豐順','person-cen-yuying':'廣西西林','person-zuo-zongtang':'湖南湘陰',
 'person-zeng-guoquan':'湖南湘鄉','person-weng-tonghe':'江蘇常熟'}
CLANS={'person-linqing':'完顏','person-chongshi':'完顏','person-wenqing':'費莫'}
UNDIVIDED={'person-hongli','person-yizhu','person-yixin','person-yihuan','person-senggelinqin'}

def compile_batch(root:Path):
    catfile=root/'data/catalog.json';c=json.loads(catfile.read_text())
    rules=json.loads((root/'data/editorial/eccp-batch-01.json').read_text())
    folder=root/'data/imports/eccp-batch-01'
    manifest={m['id']:m for m in json.loads((folder/'manifest.json').read_text())}
    refs={r['title'].removeprefix(PREFIX):r for r in json.loads((folder/'reference-openings.json').read_text()) if r['status']=='source-extracted-not-reviewed'}
    entities={e['id']:e for e in c['entities']};sources={s['id']:s for s in c['sources']}
    batch_ids={s['id'] for s in rules['sources']};old_mentions=c['mentions']
    retained=[m for m in old_mentions if m['witness'] not in batch_ids]; new_mentions=[]
    detailed={p['id']:p for f in json.loads((root/'data/people/index.json').read_text())['profiles'] for p in [json.loads((root/'data/people'/f).read_text())]}
    entries={s['person']:s['id'] for s in rules['sources']}
    # Entities exist before annotations; full person and work records are built from their occurrences below.
    for person in rules['people']:
        ident=person['id'];reference=refs.get(person.get('entry')); opening=(reference or {}).get('opening','')
        han=re.search(r'[\u3400-\u9fff]{2,6}',opening)
        label=person.get('label') or (han.group() if han else person['terms'][0])
        if ident not in entities:
            entities[ident]={'id':ident,'type':'person','label':label,'display':person.get('entry') or person['terms'][0],'aliases':[], 'life':None,'sources':[]}
    for work in rules['works']:
        entities.setdefault(work['id'],{'id':work['id'],'type':'work','label':work['title'],'display':work['title'],'aliases':work['terms'],'sources':[]})
    for spec in rules['sources']:
        wid=spec['id'];m=manifest[wid];rawpath=folder/(wid+'.response.json')
        if sha(rawpath)!=m['sha256']:raise ValueError('Source response checksum mismatch: '+wid)
        response=json.loads(rawpath.read_text())['parse']
        original=source_paragraphs(response['text']['*'])
        parts=split_paragraphs(original,spec['starts'])
        unannotated=[];working=[];layout=[]
        allrules=[{'entity':w['id'],'terms':w['terms'],'witness':wid,'note':w.get('note','Named work, publication, or titled document; source spelling preserved.')} for w in rules['works']]
        allrules += [{'entity':p['id'],'terms':p['terms'],'witness':wid} for p in rules['people']]
        allrules += [{**r,'witness':wid,'note':'Short form resolved within this biography; not a corpus-wide surname replacement.'} for r in spec['localTerms']]
        # Keep the original place / office annotations at their existing occurrences.
        old=[m for m in old_mentions if m['witness']==wid]
        for i,(node,source_paragraph) in enumerate(parts,1):
            pid=f'{wid}-{i:02}'
            local=[r for r in old if r['passage']==pid]
            rs=allrules+[{'entity':o['entity'],'terms':[o['quote']],'witness':wid,'note':o.get('note','')} for o in local if entities[o['entity']]['type'] not in {'person','work'}]
            html,mentions=annotate(node,rs,pid,local)
            working.append(html);new_mentions.extend(mentions)
            unannotated.append(f'<p id="{pid}">'+fragment(node,0,len(node.text()))+'</p>')
            kind='contributor' if node.text()=='Tu Lien-chê' else 'bibliography' if node.text().startswith('[') else 'narrative'
            layout.append({'passage':pid,'sourceParagraph':source_paragraph,'section':kind})
        textpath=root/f'data/texts/{wid}.html';upstream=root/f'data/upstream/{wid}.html'
        textpath.write_text('\n'.join(working)+'\n',encoding='utf-8');upstream.write_text('\n'.join(unannotated)+'\n',encoding='utf-8')
        s=sources.get(wid,{})
        s.update(id=wid,work='work-eccp',subject=spec['person'],title=spec['title'],shortTitle=spec['short'],language='en',text=str(textpath.relative_to(root)),upstream=str(upstream.relative_to(root)),url=url(m['title'].removeprefix(PREFIX)),revision=str(m['revision']),revisionUrl='https://en.wikisource.org/w/index.php?oldid='+str(m['revision']),edition='Hummel, ed., 1943; Wikisource transcription',extent='Complete entry, including bibliography and contributor byline; reading segments may subdivide original paragraphs.',complete=True,importMethod='MediaWiki parse response preserved. Interface/page markers removed; inline formatting and source wording retained. Reading segmentation recorded separately.',punctuation={'status':'imported','attribution':'Printed English text as transcribed on Wikisource.'},rights={'text':'PD-USGov as identified by Wikisource','transcription':'CC-BY-SA-4.0 where applicable','attribution':'Tu Lien-chê; Arthur W. Hummel, editor; Wikisource contributors'},reviewStatus='proposed',sha256=sha(textpath),upstreamSha256=sha(upstream),retrieved=m['retrieved'],rawResponse=str(rawpath.relative_to(root)),rawSha256=m['sha256'],passageLayout=layout,annotationCoverage={'people':'agent-first-pass','namedWorks':'agent-first-pass','places':'partial','events':'partial','review':'Awaiting independent review; unnamed or ambiguous role references are not silently identified.'})
        sources[wid]=s
    mentions=new_mentions+retained
    for person in rules['people']:
        ident=person['id'];ms=[m for m in mentions if m['entity']==ident]
        if not ms:raise ValueError('Declared person has no occurrence: '+ident)
        reference=refs.get(person.get('entry'));e=entities[ident]
        first=ms[0];wid=first['witness'];evidence_key='batch-evidence'
        evidence={'title':sources[wid]['shortTitle'],'url':sources[wid]['revisionUrl'],'locator':first['passage']+' · '+first['quote'],'access':'full-text','attribution':sources[wid]['rights']['attribution']}
        existing=ident in detailed
        p=copy.deepcopy(detailed[ident]) if existing else {'schemaVersion':1,'id':ident,'collection':'ECCP','reviewStatus':'agent-proposed','name':{},'life':{'birth':None,'death':None,'westernDates':[],'westernYears':[],'reportedAges':[]},'sources':{},'externalIds':{provider:{'id':None,'status':'not-searched'} for provider in ['cbdb','geni']},'accounts':[],'notes':[]}
        p['sources'][evidence_key]=evidence
        if not existing:
            n=p['name'];label=e['label'];surname=person.get('surname');given=person.get('given',label)
            if reference and ident not in UNDIVIDED:
                surname=CLANS.get(ident,label[0]);given=label if ident in CLANS else label[1:]
            n.update(surname=surname,given=given,source=evidence_key,jiguan=None,zi=[{'value':v,'source':evidence_key} for v in person.get('zi',[])],hao=[{'value':v,'source':evidence_key} for v in person.get('hao',[])],parenthetical=None,romanizations=[{'value':person.get('entry') or person['terms'][0],'system':'ECCP spelling','source':evidence_key}],note='Only sourced name components are entered. Missing native places, Chinese civil years and external IDs are unresolved.')
            if reference:
                n['source']='eccp-entry';n['romanizations'][0]['source']='eccp-entry'
                opening=reference['opening']
                heading=re.search(re.escape(label)+r'\s*\((.{0,200}?)\)',opening)
                heading=heading[1] if heading else ''
                t=re.search(r'T\.\s*([\u3400-\u9fff]+)',heading)
                hh=re.search(r'H\.\s*([\u3400-\u9fff]+)',heading)
                if t:n['zi']=[{'value':t[1],'source':'eccp-entry'}]
                if hh and not t:n['hao']=[{'value':hh[1],'source':'eccp-entry'}]
                if ident in PLACES:n['jiguan']={'label':PLACES[ident],'source':'eccp-entry','note':'Chinese rendering of the native-place expression in the ECCP opening.'}
                yr=re.search(r'(?<!\d)(1\d{3})[–-](1\d{3})',opening[:230])
                years=list(map(int,yr.groups())) if yr else [None,None]
                if not yr:
                    death=re.search(r'\bd\.[^;]{0,20}?\b(1\d{3})\b',opening[:100])
                    if death: years=[None,int(death[1])]
                person={**person,'years':years}
            for endpoint,year in zip(['birth','death'],person.get('years',[None,None])):
                if year is not None:p['life']['westernYears'].append({'event':endpoint,'calendar':'gregorian','value':year,'source':'eccp-entry' if reference else evidence_key,'status':'source-reported'})
            for kind in ['zi','hao']:
                if n[kind]:n['parenthetical']={'kind':kind,'value':n[kind][0]['value']};break
        if reference:
            p['sources']['eccp-entry']={'title':'ECCP · '+person['entry'],'url':reference['url'],'locator':'Opening paragraph; recorded revision '+str(reference['revision']),'access':'source-extracted-opening','attribution':'ECCP authors; Arthur W. Hummel, editor; Wikisource contributors'}
            acct={'source':'eccp-entry','relation':'principal-biography','url':reference['url'],'passage':entries[ident]+'-01' if ident in entries else 'Opening paragraph'}
            if ident in entries:acct['readerWitness']=entries[ident]
            p['accounts']=[a for a in p['accounts'] if a['relation']!='principal-biography']+[acct]
        elif person.get('discussedUnder'):
            target=person['discussedUnder'];p['sources']['eccp-discussion']={'title':'ECCP · '+target,'url':url(target),'locator':'Explicit see-under reference in '+first['passage'],'access':'cross-reference','attribution':'ECCP authors and Wikisource contributors'}
            p['accounts']=[a for a in p['accounts'] if a.get('source')!='eccp-discussion']+[{'source':'eccp-discussion','relation':'mentioned-in','url':url(target),'passage':'Not a principal biography of this person.'}]
        if person.get('sourceURL'):
            p['sources']['authority']={'title':'Wikisource author record','url':person['sourceURL'],'locator':'Original source author-link target','access':'source-link','attribution':'Wikisource contributors'}
        if ident in entries:p['coverage']='Complete ECCP entry imported and first-pass annotated; profile details and identifications still await independent review.'
        else:p['coverage']='Reference profile linked from the imported ECCP entries. Not a fully reviewed biography; unsearched identifiers and unknown dates remain empty.'
        p['mentions']=[{'witness':m['witness'],'passage':m['passage'],'mention':m['id'],'quote':m['quote']} for m in ms]
        detailed[ident]=p
        e['sources']=list(dict.fromkeys([*(e.get('sources') or []),*(s['id'] for s in sources.values() if s.get('subject')==ident)]))
    works=[]
    for rule in rules['works']:
        ms=[m for m in mentions if m['entity']==rule['id']]
        if not ms:raise ValueError('Declared work has no occurrence: '+rule['id'])
        sources_used={m['witness'] for m in ms}
        rec={k:v for k,v in rule.items() if k!='terms'}
        rec.update(schemaVersion=1,type='work',reviewStatus='agent-proposed',attestedTitles=list(dict.fromkeys(m['quote'] for m in ms)),sources={sid:{'title':sources[sid]['shortTitle'],'url':sources[sid]['revisionUrl'],'attribution':sources[sid]['rights']['attribution']} for sid in sorted(sources_used)},mentions=[{'witness':m['witness'],'passage':m['passage'],'mention':m['id'],'quote':m['quote']} for m in ms])
        rec.setdefault('note','This record identifies the named work, not a particular physical edition. Publication statements are source reports, not independently verified bibliographical conclusions.')
        works.append(rec);dump(root/f'data/works/{rec["id"]}.json',rec)
    c['sources']=list(sources.values());c['entities']=list(entities.values());c['mentions']=mentions
    # Add only explicitly stated kinship. Spousal and sibling relations are not parentage.
    relations=[('person-guo-songtao','person-guo-gangji','child-of'),('person-guo-kuntao','person-guo-qingfan','child-of'),('person-zeng-guofan','person-zeng-jichun','child-of'),('person-linqing','person-chonghou','child-of'),('person-linqing','person-chongshi','child-of')]
    for parent,child,predicate in relations:
        common=next((m for m in mentions if m['entity']==child and any(n['entity']==parent and n['passage']==m['passage'] and n['witness']==m['witness'] for n in mentions)),None)
        if not common:continue
        ident='r-'+child.removeprefix('person-')+'-parent'
        if not any(r['id']==ident for r in c['relations']):c['relations'].append({'id':ident,'subject':child,'predicate':predicate,'object':parent,'evidence':[{'witness':common['witness'],'passage':common['passage']}],'status':'proposed'})
    dump(catfile,c)
    for ident,p in detailed.items():dump(root/f'data/people/{ident}.json',p)
    # Preserve the subject as the first option, not alphabetical directory order.
    order=list(dict.fromkeys(['person-zeng-jize',*detailed]))
    dump(root/'data/people/index.json',{'schemaVersion':1,'profiles':[i+'.json' for i in order]})
    dump(root/'data/works/index.json',{'schemaVersion':1,'works':[w['id']+'.json' for w in works]})
    dump(root/'data/editorial/eccp-batch-01-report.json',{'batch':rules['batch'],'completeEntries':sorted(batch_ids),'people':len(detailed),'works':len(works),'mentions':len(new_mentions),'status':'agent-first-pass','limitations':['Ambiguous or unnamed role references are not silently resolved.','Place and event extraction is partial.','Source errors are preserved; independent scan collation is pending.']})
    print(json.dumps({'profiles':len(detailed),'works':len(works),'mentions':len(mentions),'completeECCP':len(batch_ids)}))
