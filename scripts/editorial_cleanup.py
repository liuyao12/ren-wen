"""Reproducible Sept 10 review: quarantine unsupported identifications, not source words.

No network access. All previous guesses remain in an evidence-linked review queue.
The Akedun case study is adjudicated only at explicit passages and occurrences.
"""
from __future__ import annotations
import json,re,hashlib,collections,html
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote
from .renwen import TextIndex
from .reading_indexes import build
ROOT=Path(__file__).resolve().parents[1]
TYPOGRAPHY='eccp-round1:work-title-typography'
IMPERIAL=set('太祖 太宗 世祖 聖祖 世宗 高宗 仁宗 宣宗 文宗 穆宗 德宗 順治 康熙 雍正 乾隆 嘉慶 道光 咸豐 同治 光緒 宣統 崇禎 萬曆 天啟 永曆 洪武 永樂 嘉靖 隆慶 正德 正統 成化 弘治 建文 泰昌 Shih-tsung Kao-tsung Shêng-tsu Hsüan-tsung Wên-tsung Mu-tsung Tê-tsung Jên-tsung T’ai-tsung T’ai-tsu'.split())

def write(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def raw(path):return path.read_text(encoding='utf-8')
def sha(text):return hashlib.sha256(text.encode('utf8')).hexdigest()
class Links(HTMLParser):
    def __init__(self,text):super().__init__();self.links=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.links.append(dict(attrs).get('href',''))
def key(url):return unquote(url).replace('_',' ').split('#')[0]

def run(root=ROOT):
    report_path=root/'data/editorial/2026-09-10-review.json'
    if report_path.exists():return json.loads(raw(report_path))
    c=json.loads(raw(root/'data/catalog.json'));ss={s['id']:s for s in c['sources']};es={e['id']:e for e in c['entities']}
    originals={};changed={};queue=[];decisions=[];kept=[]
    def text(w):
        if w not in originals:originals[w]=raw(root/ss[w]['text'])
        return changed.get(w,originals[w])
    # Explicit works attested as compilations or collected writings in Akedun's paragraph 3.
    verified_works={f'eccp-3633207-003-n{i:03}' for i in (3,5,7,9)}
    for m in c['mentions']:
        reason=None
        if m.get('origin')==TYPOGRAPHY and m['id'] not in verified_works:reason='typography-only'
        if m.get('origin')=='eccp-round1:full-attested-name-match' and m['quote'] in IMPERIAL:reason='context-dependent-imperial-name'
        if reason:
            w=m['witness'];old=text(w);pattern=rf'(<span\s+id="{re.escape(m["id"])}")\s+data-entity="{re.escape(m["entity"])}"'
            new,n=re.subn(pattern,r'\1',old);assert n==1,(m['id'],n)
            changed[w]=new
            queue.append({**m,'status':'needs-review','reason':reason,'previousSourceSha256':ss[w]['sha256'],'sourceUrl':ss[w]['revisionUrl']})
        else:
            kept.append(m)
            if m['id'] in verified_works:
                m['origin']='passage-review:akedun';m['note']='Explicit compilation or collected work in Akedun biography paragraph 3, not inferred merely from italics.'
    c['mentions']=kept;ms={m['id']:m for m in kept}
    # Correct the false cross-person identification of the one-juan chronology.
    wid='eccp-3633207';pid=wid+'-003';mid=pid+'-n011';old=next(q for q in queue if q['id']==mid)
    ident='work-akedun-nianpu';title='阿克敦年譜（ECCP 所述一卷本）'
    wrecord={'schemaVersion':1,'id':ident,'type':'work','title':title,'attestedTitles':["nien-p’u"], 'kind':'chronology','creators':[{'person':'person-eccp-3649142','role':'compiler'}],'reviewStatus':'agent-proposed','sources':{wid:{'title':ss[wid]['title'],'url':ss[wid]['revisionUrl'],'locator':pid,'attribution':'ECCP contributors; Wikisource contributors'}},'mentions':[], 'note':'Descriptive title: the one-juan chronology of Akedun compiled by Na-yen-ch’eng, mentioned with the 1816 reprint. Not the chronology of Zeng Guofan.'}
    es[ident]={'id':ident,'type':'work','label':title,'display':title,'sources':[wid],'aliases':[]};c['entities'].append(es[ident])
    changed[wid]=text(wid).replace(f'<span id="{mid}">',f'<span id="{mid}" data-entity="{ident}">',1)
    replacement={**{k:v for k,v in old.items() if k in {'id','witness','passage','quote'}},'entity':ident,'status':'proposed','origin':'passage-review:akedun','note':wrecord['note']}
    c['mentions'].append(replacement);queue.remove(old);decisions.append({'operation':'relink','before':old,'after':replacement})
    # Canonical biography IDs, not the duplicate profiles of printed temple-name notices.
    kangxi='person-eccp-3639989';yongzheng='person-eccp-3678153';qianlong='person-hongli'
    def add(w,p,needle,quote,target):
        value=text(w);start=value.index(f'<p id="{p}">');end=value.index('</p>',start)
        para=value[start:end];plain=TextIndex(value).passages[p]
        assert plain.count(needle)==1,(p,needle)
        pieces=[];positions=[]
        for token in re.finditer(r'<[^>]*>|&[^;\s]+;|[^<&]+|[<&]',para):
            chunk=token.group()
            if chunk.startswith('<') and chunk.endswith('>'):continue
            decoded=html.unescape(chunk)
            for i,ch in enumerate(decoded):
                pieces.append(ch);positions.append((token.start()+i,token.start()+i+1) if decoded==chunk else (token.start(),token.end()))
        assert ''.join(pieces)==plain,(p,'text mapping')
        at=plain.index(needle)+needle.index(quote);lo=positions[at][0];hi=positions[at+len(quote)-1][1]
        assert html.unescape(para[lo:hi])==quote
        new_id=p+'-review-'+str(sum(m['passage']==p and m.get('origin')=='passage-review:akedun' for m in c['mentions'])+1).zfill(3)
        assert target in es
        para=para[:lo]+f'<span id="{new_id}" data-entity="{target}">'+para[lo:hi]+'</span>'+para[hi:]
        changed[w]=value[:start]+para+value[end:]
        m={'id':new_id,'witness':w,'passage':p,'quote':quote,'entity':target,'status':'proposed','origin':'passage-review:akedun','note':'Occurrence identified within the explicitly dated narrative; not a global title alias.'}
        c['mentions'].append(m);decisions.append({'operation':'annotate','after':m,'context':needle})
    add(wid,wid+'-001','the emperor in 1726','the emperor',yongzheng)
    add(wid,wid+'-002','the emperor was journey','the emperor',qianlong)
    q='qsg-volume-303'
    for num,needles,target in [(21,['上以阿克敦'],kangxi),(22,['上嘉阿克敦','上為寢','上諭嘉之'],yongzheng),(23,['上以士俊','上遣通政使','上命釋'],yongzheng),(24,['上命撫遠','上以阿克敦'],yongzheng),(25,['上謂游牧'],qianlong),(26,['上以為大誤','上怒','連歲上幸','上遣醫'],qianlong)]:
        for needle in needles:add(q,f'{q}-{num:03}',needle,'上',target)
    # Restore the reviewed temple-name occurrences using their stable mention IDs.
    for p,quote,target in [(q+'-021','世宗',yongzheng),(q+'-024','高宗',qianlong)]:
        matches=[m for m in queue if m['passage']==p and m['quote']==quote];assert len(matches)==1,(p,quote)
        m=matches[0];queue.remove(m);value=text(q);changed[q]=value.replace(f'<span id="{m["id"]}">',f'<span id="{m["id"]}" data-entity="{target}">',1)
        new={k:m[k] for k in ['id','witness','passage','quote']};new.update(entity=target,status='proposed',origin='passage-review:akedun',note='Accession explicitly identifies the Qing emperor within this account.');c['mentions'].append(new);decisions.append({'operation':'relink','before':m,'after':new})
    # Preserve every word, tag, paragraph and original source revision.
    for w,new in changed.items():
        assert TextIndex(new).passages==TextIndex(originals[w]).passages,w
        (root/ss[w]['text']).write_text(new);ss[w]['sha256']=sha(new)
    c['mentions'].sort(key=lambda m:(m['witness'],m['passage'],m['id']))
    active=collections.defaultdict(list);quarantined=collections.defaultdict(list)
    for m in c['mentions']:active[m['entity']].append(m)
    for m in queue:quarantined[m['entity']].append(m)
    index=json.loads(raw(root/'data/works/index.json'));index['works'].append(ident+'.json')
    for file in index['works']:
        p=wrecord if file==ident+'.json' else json.loads(raw(root/'data/works'/file))
        p['mentions']=[{'witness':m['witness'],'passage':m['passage'],'mention':m['id'],'quote':m['quote']} for m in active[p['id']]]
        if quarantined[p['id']]:p['quarantinedMentions']=[m['id'] for m in quarantined[p['id']]]
        if not p['mentions']:
            p['identificationStatus']='needs-review';p['note']='Typography-only candidate, withheld from ordinary reading links pending contextual identification. This may be a title, rank, term, or other italic expression.'
        else:p.pop('identificationStatus',None)
        write(root/'data/works'/file,p)
    write(root/'data/works/index.json',index)
    # Resolve printed notices as navigation only, never as a person-identity merge.
    urls={key(s['url']):s['id'] for s in c['sources']};redirects={};unresolved=[]
    for s in c['sources']:
        if s.get('kind')!='cross-reference':continue
        targets=list(dict.fromkeys(urls[k] for u in Links(raw(root/s['upstream'])).links if (k:=key(u)) in urls and urls[k]!=s['id']))
        if len(targets)==1:redirects[s['id']]={'target':targets[0],'relation':'printed-cross-reference','person':s.get('subject')}
        else:
            explicit={'eccp-3633195':'eccp-3639274','eccp-3637583':'eccp-3639264','eccp-3649140':'eccp-3639274','eccp-3658553':'eccp-3639271','eccp-3658563':'eccp-3639264','eccp-3678132':'eccp-3639264','eccp-3678485':'eccp-3678174'}.get(s['id'])
            if explicit:
                assert explicit in ss and ss[explicit].get('kind')!='cross-reference'
                redirects[s['id']]={'target':explicit,'relation':'printed-cross-reference','person':s.get('subject')}
            else:unresolved.append({'source':s['id'],'targets':targets})
    c['navigation']={'redirects':redirects,'unresolvedRedirects':unresolved}
    collection=json.loads(raw(root/'data/collections/eccp.json'))
    aliases=collections.defaultdict(list)
    for e in collection['entries']:
        if e['source'] not in redirects:continue
        target=redirects[e['source']]['target'];seen={e['source']}
        while target in redirects and target not in seen:seen.add(target);target=redirects[target]['target']
        if target not in seen:aliases[target].append(e['title'])
    for entry in unresolved:
        for target in entry['targets']:aliases[target].append(ss[entry['source']]['title'].split(' · ')[0])
    for e in collection['entries']:e['searchAliases']=aliases.get(e['source'],[])
    collection['counts']['mentions']=len(c['mentions']);collection['counts']['works']=len(index['works'])
    write(root/'data/catalog.json',c);write(root/'data/collections/eccp.json',collection)
    write(root/'data/editorial/identification-review.json',{'schemaVersion':1,'decisions':decisions,'quarantined':queue})
    report={'release':'2026-09-10','textWordsChanged':0,'quarantined':len(queue),'byReason':dict(collections.Counter(m['reason'] for m in queue)),'focusedDecisions':len(decisions),'activeMentions':len(c['mentions']),'activeWorkProfiles':sum(bool(v) for k,v in active.items() if es[k]['type']=='work'),'redirects':len(redirects),'unresolvedRedirects':unresolved,'scope':'Only Akedun passages and the listed unsupported import mechanisms; not a full corpus review.'}
    write(report_path,report);build(root);return report
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))
