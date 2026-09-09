"""Append one explicitly annotated complete ECCP entry, never rebuild older entries.

Run in a Git worktree. The preserved response and a source manifest are required.
Unsupported block content causes a hard failure, never a silent omission.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re
from pathlib import Path
from urllib.parse import quote
from .eccp_batch import Tree, nodes, clean, source_paragraphs, fragment, annotate
from .eccp_compile import dump, url

ROOT=Path(__file__).resolve().parents[1]
def digest(raw):return hashlib.sha256(raw).hexdigest()
def compact(text):return ''.join(text.split())
def complete_paragraphs(html):
    tree=Tree(html).root
    bodies=[n for n in nodes(tree) if 'prp-pages-output' in n.attrs.get('class','').split()]
    if len(bodies)!=1:raise ValueError('Expected one scan-backed reading body')
    paragraphs=source_paragraphs(html)
    whole=compact(clean(bodies[0]).text())
    if whole!=compact(''.join(n.text() for n in paragraphs)):
        raise ValueError('Unrepresented block text: extend the importer, do not omit it')
    if not paragraphs:raise ValueError('Empty entry')
    return paragraphs,whole

def import_entry(spec_path, raw_path, manifest_path, root=ROOT):
    spec=json.loads(spec_path.read_text());raw=raw_path.read_bytes();meta=json.loads(manifest_path.read_text())
    c=json.loads((root/'data/catalog.json').read_text());wid=spec['id']
    if any(s['id']==wid for s in c['sources']):raise ValueError('Entry already exists; use reviewed source-version merging')
    if meta['sha256']!=digest(raw):raise ValueError('Source checksum mismatch')
    response=json.loads(raw)['parse'];ps,whole=complete_paragraphs(response['text']['*'])
    if response['title']!="Eminent Chinese of the Ch'ing Period/"+spec['entry']:raise ValueError('Wrong entry response')
    if ps[-1].text()!=spec['author']:raise ValueError('Byline not retained or wrong contributor')
    entities={e['id']:e for e in c['entities']}
    people={p['id']:p for f in json.loads((root/'data/people/index.json').read_text())['profiles'] for p in [json.loads((root/'data/people'/f).read_text())]}
    works={w['id']:w for f in json.loads((root/'data/works/index.json').read_text())['works'] for w in [json.loads((root/'data/works'/f).read_text())]}
    for p in spec['people']:entities.setdefault(p['id'],{'id':p['id'],'type':'person','label':p.get('label',p['terms'][0]),'display':p.get('entry',p['terms'][0]),'aliases':[],'life':None,'sources':[]})
    for w in spec['works']:entities.setdefault(w['id'],{'id':w['id'],'type':'work','label':w['title'],'display':w['title'],'aliases':w['terms'],'sources':[]})
    base=[];working=[];mentions=[];layout=[]
    for i,n in enumerate(ps,1):
        pid=f'{wid}-{i:02}'
        rules=[{'entity':w['id'],'terms':w['terms'],'witness':wid,'note':'Named work; title identifies the work, not necessarily a particular edition.'} for w in spec['works'] if not w.get('passages') or i in w['passages']]
        rules += [{'entity':p['id'],'terms':p['terms'],'witness':wid} for p in spec['people']]
        rules += [{**r,'witness':wid,'note':'Context-specific short form; not a global substitution.'} for r in spec.get('scoped',[]) if i in r['passages']]
        marked,ms=annotate(n,rules,pid,[])
        for m in ms:m['origin']=wid+'-first-pass'
        mentions+=ms;working.append(marked);base.append(f'<p id="{pid}">'+fragment(n,0,len(n.text()))+'</p>')
        kind='contributor' if i==len(ps) else 'bibliography' if i==len(ps)-1 else 'narrative'
        layout.append({'passage':pid,'sourceParagraph':i,'section':kind,'characters':len(n.text())})
    # No annotation can remove even a single source character.
    if compact(''.join(Tree(x).root.text() for x in working))!=whole:raise ValueError('Annotation changed source wording')
    folder=root/'data/imports'/wid;folder.mkdir(parents=True,exist_ok=True)
    (folder/'response.json').write_bytes(raw);dump(folder/'manifest.json',meta)
    text='\n'.join(working)+'\n';baseline='\n'.join(base)+'\n'
    (root/f'data/texts/{wid}.html').write_text(text);(root/f'data/upstream/{wid}.html').write_text(baseline)
    s={'id':wid,'work':'work-eccp','subject':spec['subject'],'title':spec['entry']+' '+entities[spec['subject']]['label'],'shortTitle':'ECCP · '+entities[spec['subject']]['label'],'language':'en','text':f'data/texts/{wid}.html','upstream':f'data/upstream/{wid}.html','url':url(spec['entry']),'revision':str(response['revid']),'revisionUrl':'https://en.wikisource.org/w/index.php?oldid='+str(response['revid']),'edition':'Hummel, ed., 1943; Wikisource transcription','extent':'Complete entry, including all 17 source paragraphs, bibliography and contributor byline.','complete':True,'importMethod':'One-entry import of a preserved MediaWiki response; entire reading-body text checked against every imported paragraph. Inline formatting retained; page-number interface markers removed.','punctuation':{'status':'imported','attribution':'Printed English punctuation as transcribed by Wikisource.'},'rights':{'text':'PD-USGov as identified by Wikisource','transcription':'CC-BY-SA-4.0 where applicable','attribution':spec['author']+'; Arthur W. Hummel, editor; Wikisource contributors'},'reviewStatus':'proposed','retrieved':meta['retrieved'],'sha256':digest(text.encode()),'upstreamSha256':digest(baseline.encode()),'rawResponse':str((folder/'response.json').relative_to(root)),'rawSha256':digest(raw),'passageLayout':layout,'completeness':{'method':'full-reading-body-versus-imported-paragraphs','paragraphs':len(ps),'normalizedBodySha256':digest(whole.encode()),'normalizedCharacters':len(whole),'byline':spec['author'],'bibliographyPassage':layout[-2]['passage']},'annotationCoverage':{'people':'agent-first-pass','namedWorks':'agent-first-pass','places':'not-yet-annotated','events':'not-yet-extracted','review':'Unresolved role references recorded in the editorial specification.'}}
    s['extent']=f'Complete entry: {len(ps)} source paragraphs, bibliography and contributor byline; no text omitted.'
    c['sources'].append(s);c['mentions']+=mentions;c['entities']=list(entities.values())
    def source_evidence(ms):return {'title':s['shortTitle'],'url':s['revisionUrl'],'locator':'; '.join(dict.fromkeys(m['passage'] for m in ms)),'access':'full-text','attribution':s['rights']['attribution']}
    for person in spec['people']:
        ident=person['id'];ms=[m for m in mentions if m['entity']==ident]
        if not ms:
            # A rule not used is an editorial error, not permission to invent an occurrence.
            raise ValueError('Person rule has no occurrence: '+ident)
        new=ident not in people
        if new:
            label=person['label'];han=bool(re.fullmatch('[\u3400-\u9fff]+',label));surname=label[0] if han and not person.get('undivided') else None;given=label[1:] if surname else label
            p={'schemaVersion':1,'id':ident,'collection':'ECCP','reviewStatus':'agent-proposed','coverage':'Source-linked reference profile; full biographical and external-ID review pending.','name':{'surname':surname,'given':given,'source':wid,'jiguan':None,'zi':[{'value':z,'source':wid} for z in person.get('zi',[])],'hao':[],'parenthetical':{'kind':'zi','value':person['zi'][0]} if person.get('zi') else None,'romanizations':[{'value':person.get('entry',person['terms'][0]),'system':'ECCP spelling','source':wid}],'note':'Only attested components entered. Unresolved Chinese identity, native place, dates and external IDs are not invented.'},'life':{'birth':None,'death':None,'westernDates':[],'westernYears':[{'event':e,'calendar':'gregorian','value':y,'source':wid,'status':'source-reported'} for e,y in zip(['birth','death'],person.get('years',[None,None])) if y is not None],'reportedAges':[]},'externalIds':{k:{'id':None,'status':'not-searched'} for k in ['cbdb','geni']},'accounts':[],'sources':{},'notes':[]}
        else:p=copy.deepcopy(people[ident])
        p['sources'][wid]=source_evidence(ms)
        p.setdefault('mentions',[]).extend({'witness':m['witness'],'passage':m['passage'],'mention':m['id'],'quote':m['quote']} for m in ms)
        if person.get('entry') and not any(a['relation']=='principal-biography' for a in p['accounts']):
            p['sources']['eccp-cross-reference']={'title':'ECCP · '+person['entry'],'url':url(person['entry']),'locator':'Existing ECCP cross-reference; entry not imported here.','access':'cross-reference','attribution':'ECCP authors and Wikisource contributors'}
            p['accounts'].append({'source':'eccp-cross-reference','relation':'principal-biography','url':url(person['entry']),'passage':'ECCP cross-reference destination'})
        if ident==spec['subject']:
            p['accounts']=[a for a in p['accounts'] if a['relation']!='principal-biography']+[{'source':wid,'relation':'principal-biography','readerWitness':wid,'passage':wid+'-01'}]
            p['coverage']='Complete ECCP biography imported with all paragraphs, bibliography and byline. Person and work markup is a first-pass proposal; event and place extraction is pending.'
            entities[ident]['sources']=list(dict.fromkeys(entities[ident].get('sources',[])+[wid]))
        if person.get('discussedUnder') and not any(a['relation']=='mentioned-in' for a in p['accounts']):
            key='eccp-discussion';p['sources'][key]={'title':'ECCP · '+person['discussedUnder'],'url':url(person['discussedUnder']),'locator':'See-under cross-reference in '+ms[0]['passage'],'access':'cross-reference','attribution':'ECCP contributors'}
            p['accounts'].append({'source':key,'relation':'mentioned-in','url':url(person['discussedUnder']),'passage':'Not a principal biography'})
        people[ident]=p
    for rule in spec['works']:
        ident=rule['id'];ms=[m for m in mentions if m['entity']==ident]
        if not ms:raise ValueError('Work rule has no occurrence: '+ident)
        w=copy.deepcopy(works.get(ident,{k:v for k,v in rule.items() if k not in {'terms','passages'}}))
        w.update(schemaVersion=1,type='work',reviewStatus=w.get('reviewStatus','agent-proposed'))
        w.setdefault('sources',{})[wid]=source_evidence(ms)
        w.setdefault('mentions',[]).extend({'witness':wid,'passage':m['passage'],'mention':m['id'],'quote':m['quote']} for m in ms)
        w['attestedTitles']=list(dict.fromkeys(w.get('attestedTitles',[])+[m['quote'] for m in ms]))
        w.setdefault('note','Work identity and reported publication information from ECCP. An editorial descriptive title is not a newly asserted historical title.')
        works[ident]=w
    dump(root/'data/catalog.json',c)
    for ident,p in people.items():dump(root/f'data/people/{ident}.json',p)
    for ident,w in works.items():dump(root/f'data/works/{ident}.json',w)
    dump(root/'data/people/index.json',{'schemaVersion':1,'profiles':[i+'.json' for i in people]})
    dump(root/'data/works/index.json',{'schemaVersion':1,'works':[i+'.json' for i in works]})
    report={'entry':wid,'complete':s['completeness'],'newMentions':len(mentions),'peopleInEntry':len({m['entity'] for m in mentions if entities[m['entity']]['type']=='person'}),'worksInEntry':len({m['entity'] for m in mentions if entities[m['entity']]['type']=='work'}),'unresolved':spec.get('unresolved',[]),'status':'agent-first-pass'}
    dump(root/f'data/editorial/{wid}-report.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec',type=Path);p.add_argument('response',type=Path);p.add_argument('manifest',type=Path);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    print(json.dumps(import_entry(a.spec,a.response,a.manifest,a.root),ensure_ascii=False,indent=2))
