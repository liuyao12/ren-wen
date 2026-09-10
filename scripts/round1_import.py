"""Reproducible first-round corpus import from preserved MediaWiki responses.

Full source text is imported independently of the necessarily provisional name
recognition pass. Existing edited witnesses and occurrence identifiers are kept.
Run only on a review worktree; publication is a separate Git operation.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re, shutil, unicodedata
from collections import Counter, defaultdict, deque
from html import escape
from pathlib import Path
from urllib.parse import unquote, urljoin, quote
from .eccp_batch import Node, Tree, nodes, fragment
from .renwen import TextIndex

ROOT=Path(__file__).resolve().parents[1]
PREFIX="Eminent Chinese of the Ch'ing Period/"
ANCILLARY={'Preface',"Editor's Note",'Contributors of Biographical Sketches',"A Note on Ch'üan Tsu-wang, Chao I-ch'ing and Tai Chên",'Corrections',"Thirty-three Collections of Ch'ing Dynasty Biographies"}
HAN=r'[\u3400-\u9fff]'
INLINE={'i','b','em','strong','sup','sub','br','a'}
BLOCK={'p','div','section','blockquote','ul','ol','li','table','thead','tbody','tfoot','tr','td','th','h1','h2','h3','h4','h5','h6','dl','dt','dd'}
IGNORED={'script','style','img','hr','link','meta'}
DROP_CLASSES={'ws-pagenum','mw-editsection','catlinks','printfooter','navbox','licenseContainer','licensetpl','noprint','header-template'}
DATE=re.compile(r'(?<!\d)(1[0-9]{3}|[3-9][0-9]{2})(\??)\s*[–—−-]\s*(1[0-9]{3}|[3-9][0-9]{2})(\??)')
COMPOUNDS={'歐陽','司馬','上官','諸葛','夏侯','司徒','司空','皇甫','東方','尉遲','公孫','令狐'}
NOT_WORK={'sui','chüan','chüan,','chin-shih','chü-jên','hsiu-ts’ai','hsiu-ts\'ai','ching','shih','tzu','chi','tao','li','hsien','chin','tael','taels','tsung-tu','hsün-fu','tao-t\'ai','pu-chêng shih','beile','beise','hou','kung','wang','q. v.','qq. v.','q.v.','qq.v.','ibid.','et al.','etc.','fu','hsien','nien-hao','shih','t.','h.','a','b','c','d','e','f','g','h','i','ii','iii','iv'}
PROVINCES=['直隸','奉天','吉林','黑龍江','江蘇','安徽','山西','山東','河南','陝西','甘肅','浙江','福建','江西','湖北','湖南','廣東','廣西','四川','雲南','貴州','順天','京師']

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def compact(s):return ''.join(s.split()).replace('\u200b','')
def norm(s):return re.sub(r'\s+',' ',unicodedata.normalize('NFC',s)).strip().casefold()
def slug(s):
    x=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub('[^a-z0-9]+','-',x).strip('-') or 'reference'
def url(title,lang='en'):return f'https://{lang}.wikisource.org/wiki/'+quote(title.replace(' ','_'),safe='/')
def article_key(u):
    try:
        title=unquote(u.split('/wiki/',1)[1]).replace('_',' ')
        return title.split('#')[0] if title.startswith(PREFIX) else None
    except (IndexError,AttributeError):return None

def body_clean(n,lang='en'):
    if isinstance(n,str):return re.sub(r'[\t\r\n ]+',' ',n).replace('\u200b','')
    classes=set(n.attrs.get('class','').split())
    if n.tag in IGNORED or classes & DROP_CLASSES or n.attrs.get('id') in {'headerContainer','header','toc','licenseContainer','catlinks'}:return ''
    attrs={}
    if n.tag=='a':
        u=urljoin(f'https://{lang}.wikisource.org',n.attrs.get('href',''))
        if u.startswith(('https://','http://')):attrs['href']=u
    return Node(n.tag if n.tag in INLINE|BLOCK else '',attrs,[body_clean(c,lang) for c in n.children])

def reading_blocks(html,lang='en'):
    """Retain reading text outside p tags, including footnotes and tables.

    Presentation blocks become sequential paragraphs, with original inline
    emphasis/links retained. Comparison is against the ENTIRE reading body.
    """
    tree=Tree(html).root
    bodies=[n for n in nodes(tree) if 'prp-pages-output' in n.attrs.get('class','').split()]
    if not bodies:
        if lang=='en':raise ValueError('No scan-backed reading body')
        bodies=[next(n for n in nodes(tree) if 'mw-parser-output' in n.attrs.get('class','').split())]
    cleaned=Node('',{},[body_clean(b,lang) for b in bodies])
    groups=[];buffer=[]
    def flush():
        nonlocal buffer
        n=Node('',{},buffer);buffer=[]
        if n.text().strip():
            text=n.text();a=len(text)-len(text.lstrip());b=len(text.rstrip())
            groups.append(Tree(fragment(n,a,b)).root)
    def visit(n):
        if isinstance(n,str):buffer.append(n);return
        if n.tag in BLOCK:
            flush()
            for c in n.children:visit(c)
            flush()
        else:
            # Wrapper containing blocks must be recursed, not flattened.
            if any(x.tag in BLOCK for x in nodes(n)):
                for c in n.children:visit(c)
            else:buffer.append(n)
    visit(cleaned);flush()
    whole=compact(cleaned.text());joined=compact(''.join(n.text() for n in groups))
    if whole!=joined:raise ValueError('Unrepresented source text')
    if not whole:raise ValueError('Empty source')
    return groups,whole

def toc_rows(root):
    obj=json.load(open(root/'eccp-index.response.json'))['parse'];text=obj['wikitext']['*'];result={}
    for line in text.splitlines():
        m=re.match(r"\*\s*('')?\[\[/([^]|]+?)/?(?:\|[^]]+)?\]\]('')?\s*(.*)",line)
        if m:
            title=m[2].strip().strip('/');result[title]={'kind':'reference-material' if title in ANCILLARY else 'cross-reference' if m[1] else 'biography','label':m[4]}
    return result

def basic_profile(ident,label,source,roman=None,undivided=False):
    han=re.fullmatch(HAN+'{2,6}',label);surname=None
    if han and not undivided:
        surname=label[:2] if label[:2] in COMPOUNDS else label[:1]
    return {'schemaVersion':1,'id':ident,'collection':'ECCP','reviewStatus':'agent-proposed','coverage':'First-round reference profile; identification and biographical details await review.',
      'name':{'surname':surname,'given':label[len(surname):] if surname else label,'source':source,'jiguan':None,'bracket':None,'registration':{'attestations':[]},'zi':[],'hao':[],'parenthetical':None,'romanizations':[{'value':roman,'system':'ECCP spelling','source':source}] if roman else []},
      'life':{'birth':None,'death':None,'westernDates':[],'westernYears':[],'reportedAges':[]},'externalIds':{k:{'id':None,'status':'not-searched'} for k in ['cbdb','geni']},'accounts':[],'sources':{},'notes':[]}

def title_label(title,entry,opening):
    if title=='Abahai':return '皇太極'
    m=re.search(HAN+'{2,8}',entry.get('label',''))
    if m:return m[0]
    # First attested Han form only when it immediately follows the printed name.
    m=re.match(r"[^,，(（\d]{1,65}?\s+("+HAN+r'{2,8})(?=[ ,，(（])',opening)
    return m[1] if m else title

def enrich_opening(p,opening,key):
    # This is deliberately limited to the subject's introductory name clause.
    intro=opening[:opening.find('),')+2] if '),' in opening[:350] else opening[:300]
    for kind,mark in [('zi','T.'),('hao','H.')]:
        m=re.search(re.escape(mark)+r'\s*('+HAN+r'{1,10}(?:\s*[,、]\s*'+HAN+r'{1,10})*)',intro)
        if m and not p['name'].get(kind):p['name'][kind]=[{'value':v.strip(),'source':key} for v in re.split('[,、]',m[1])]
    if not p['name'].get('parenthetical'):
        for kind in ['zi','hao']:
            if p['name'].get(kind):p['name']['parenthetical']={'kind':kind,'value':p['name'][kind][0]['value']};break
    head=re.split(r'\b(?:was|whose|his father|her father|son of|daughter of|His|Her)\b',opening[:300],maxsplit=1)[0]
    m=DATE.search(head)
    if m and not p['life'].get('westernDates') and not p['life'].get('westernYears'):
        p['life']['westernYears']=[{'event':event,'calendar':'gregorian','value':int(y),'source':key,'status':'source-reported','uncertain':bool(q),'note':'Western year as printed; not a resolved Chinese civil year.'} for event,y,q in [('birth',m[1],m[2]),('death',m[3],m[4])]]
    m=re.search(r'(?:member of the |came from the |of the )[^.]{0,60}?('+HAN+r'{2,6})\s+clan',opening[:420])
    if m:
        p['name']['clan']={'label':m[1],'source':key};p['name']['bracket']={'kind':'clan','label':m[1],'source':key}
        # A Manchu clan is not prepended as a Han-style surname.
        label=(p['name'].get('surname') or '')+p['name']['given'];p['name']['surname']=None;p['name']['given']=label
    intro_sent=opening[:min(700,opening.find('. ',180)+1 if opening.find('. ',180)>=0 else 700)]
    if re.search(r'native of|Banner|clan',intro_sent):
        at={'text':intro_sent.strip(),'source':key,'kind':'source-wording','status':'imported'}
        reg=p['name'].setdefault('registration',{'attestations':[]})
        if not any(x['text']==at['text'] for x in reg['attestations']):reg['attestations'].append(at)

class NameMatcher:
    """Aho–Corasick matcher: linear in source length, no external dependency."""
    def __init__(self, terms):
        self.go=[{}];self.fail=[0];self.out=[[]]
        for term in terms:
            at=0
            for ch in term:
                if ch not in self.go[at]:
                    self.go[at][ch]=len(self.go);self.go.append({});self.fail.append(0);self.out.append([])
                at=self.go[at][ch]
            self.out[at].append(term)
        q=deque(self.go[0].values())
        while q:
            r=q.popleft()
            for ch,u in self.go[r].items():
                q.append(u);v=self.fail[r]
                while v and ch not in self.go[v]:v=self.fail[v]
                self.fail[u]=self.go[v].get(ch,0);self.out[u].extend(self.out[self.fail[u]])
    def find(self,text):
        folded=''.join(' ' if c.isspace() else c.casefold() for c in text)
        positions=None
        if len(folded)!=len(text):
            positions=[]
            for i,c in enumerate(text):positions.extend([i]*len(' ' if c.isspace() else c.casefold()))
        at=0
        for i,ch in enumerate(folded):
            while at and ch not in self.go[at]:at=self.fail[at]
            at=self.go[at].get(ch,0)
            for term in self.out[at]:
                a=i-len(term)+1;b=i+1
                if positions:a,b=positions[a],positions[b-1]+1
                yield a,b,term

class Importer:
    def __init__(self,root,raw,qsg):
        self.root,self.raw,self.qsg=root,raw,qsg
        self.c=json.load(open(root/'data/catalog.json'))
        self.people={p['id']:p for f in json.load(open(root/'data/people/index.json'))['profiles'] for p in [json.load(open(root/'data/people'/f))]}
        for p in self.people.values():
            n=p['name']
            if n.get('surname')=='完顏':
                n['clan']={'label':'完顏','source':n['source']};n['bracket']={'kind':'clan','label':'完顏','source':n['source']};n['surname']=None
        self.works={w['id']:w for f in json.load(open(root/'data/works/index.json'))['works'] for w in [json.load(open(root/'data/works'/f))]}
        self.entities={e['id']:e for e in self.c['entities']};self.sources={s['id']:s for s in self.c['sources']}
        self.article_people={};self.existing_sources={article_key(s.get('url')):s for s in self.c['sources'] if article_key(s.get('url'))}
        for p in self.people.values():
            for a in p['accounts']:
                if a['relation']=='principal-biography':
                    k=article_key(a.get('url') or p['sources'].get(a['source'],{}).get('url'))
                    if k:self.article_people.setdefault(k,p['id'])
        self.toc=toc_rows(raw);self.documents=[];self.terms=defaultdict(set);self.evidence=[];self.qmatches=[]
        self.by_work=defaultdict(set)
        for w in self.works.values():
            for t in [w['title']]+w.get('attestedTitles',[]):self.by_work[norm(t)].add(w['id'])
        for p in self.people.values():
            for t in [(p['name'].get('surname') or '')+p['name']['given']]+[x['value'] for x in p['name'].get('romanizations',[])]:self.terms[norm(t)].add(p['id'])
    def evidence_source(self,wid,passage):
        s=self.sources[wid]
        return {'title':s['shortTitle'],'url':s['revisionUrl'],'locator':passage,'access':'full-text','attribution':s['rights']['attribution']}
    def source_record(self,wid,row,kind,subject,lang,blocks,whole):
        title=row['title'];qsg=lang=='zh';rawpath=f'data/imports/round1/{"qsg" if qsg else "eccp"}/{row["pageid"]}.json'
        origin=(self.qsg if qsg else self.raw)/row['path'];target=self.root/rawpath;target.parent.mkdir(parents=True,exist_ok=True)
        raw=origin.read_bytes()
        if sha(raw)!=row['sha256']:raise ValueError('Source checksum mismatch '+title)
        target.write_bytes(raw)
        label=self.entities.get(subject,{}).get('label',title.split('/')[-1])
        return {'id':wid,'work':'work-qingshigao' if qsg else 'work-eccp','subject':subject,'title':title.split('/')[-1]+(' · '+label if subject else ''),'shortTitle':title if qsg else 'ECCP · '+label,'language':'zh-Hant' if qsg else 'en','kind':kind,'text':f'data/texts/{wid}.html','upstream':f'data/upstream/{wid}.html','url':url(title,'zh' if qsg else 'en'),'revision':str(row['revision']),'revisionUrl':f'https://{"zh" if qsg else "en"}.wikisource.org/w/index.php?oldid={row["revision"]}','edition':'Wikisource transcription; printed QSG edition not identified' if qsg else 'Arthur W. Hummel, ed., 1943; Wikisource transcription','complete':True,'extent':f'Complete reading body ({len(blocks)} blocks); nothing abridged. Website navigation omitted.','importMethod':'Full preserved parse response; reading blocks include paragraph continuations and notes. Source wording unchanged.','punctuation':{'status':'imported','attribution':'Wikisource punctuation; editor not identified.' if qsg else 'Printed English punctuation as transcribed on Wikisource.'},'rights':{'text':'Public-domain historical work' if qsg else 'PD-USGov as identified by Wikisource','transcription':'CC-BY-SA-4.0 where applicable','attribution':'Wikisource contributors; 清史稿編纂者' if qsg else 'ECCP contributors; Arthur W. Hummel, editor; Wikisource contributors'},'reviewStatus':'proposed','retrieved':row['retrieved'],'rawResponse':rawpath,'rawSha256':row['sha256'],'completeness':{'method':'whole-reading-body','normalizedBodySha256':sha(whole.encode()),'normalizedCharacters':len(whole),'paragraphs':len(blocks)},'annotationCoverage':{'people':'automated-first-pass','namedWorks':'automated-first-pass','places':'partial','events':'not-yet-extracted','review':'Recognition and identity resolution await passage-by-passage review.'}}
    def register_entity(self,p):
        n=p['name'];label=(n.get('surname') or '')+n['given']
        self.entities.setdefault(p['id'],{'id':p['id'],'type':'person','label':label,'display':label,'aliases':[],'life':None,'sources':[]})
    def prepare(self):
        manifest=json.load(open(self.raw/'manifest.json'))
        for row in manifest:
            if row.get('status')!='downloaded-not-reviewed':raise ValueError('Missing source '+row['title'])
            destination=self.root/f'data/imports/round1/eccp/{row["pageid"]}.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes((self.raw/row['path']).read_bytes())
            entry=row['title'][len(PREFIX):];toc=self.toc[entry];obj=json.load(open(self.raw/row['path']))['parse'];blocks,whole=reading_blocks(obj['text']['*'])
            kind=toc['kind'];existing=self.existing_sources.get(row['title']);wid=existing['id'] if existing else 'eccp-'+str(row['pageid']);subject=None
            if kind!='reference-material':
                label=title_label(entry,toc,blocks[0].text());subject=self.article_people.get(row['title'])
                if not subject:
                    candidates=self.terms.get(norm(label),set()) | self.terms.get(norm(entry),set())
                    subject=next(iter(candidates)) if len(candidates)==1 else 'person-eccp-'+str(row['pageid'])
                if subject not in self.people:self.people[subject]=basic_profile(subject,label,wid,entry,undivided=(' ' not in entry))
                self.article_people[row['title']]=subject
                p=self.people[subject];self.register_entity(p)
                self.terms[norm(label)].add(subject);self.terms[norm(entry)].add(subject)
                if not existing:
                    p['sources'][wid]={'title':'ECCP · '+entry,'url':f'https://en.wikisource.org/w/index.php?oldid={row["revision"]}','locator':wid+'-001','access':'full-text','attribution':'ECCP authors and Wikisource contributors'}
                    if kind=='biography':
                        p['accounts'].append({'source':wid,'relation':'principal-biography','readerWitness':wid,'passage':wid+'-001'})
                        enrich_opening(p,blocks[0].text(),wid)
                    else:
                        p['accounts'].append({'source':wid,'relation':'cross-reference-entry','readerWitness':wid,'passage':wid+'-001'})
            if not existing:self.sources[wid]=self.source_record(wid,row,kind,subject,'en',blocks,whole)
            self.documents.append({'wid':wid,'row':row,'entry':entry,'kind':kind,'subject':subject,'blocks':blocks,'whole':whole,'existing':bool(existing)})
        # All entry headings are indexed before processing their cross-references.
        names=[t for t,ids in self.terms.items() if len(ids)==1 and ((len(t)>=2 and re.fullmatch(HAN+'+',t)) or (len(t)>2 and (' ' in t or '-' in t)))]
        self.name_matcher=NameMatcher(names)
        self.roman_pattern=re.compile(r"(?<![\w])(?:[A-ZÀ-Þ][a-zà-ÿ'’ʻ-]{1,18})\s+(?:[A-ZÀ-Þ][a-zà-ÿ'’ʻ]+(?:-[a-zà-ÿ'’ʻ]+){1,3})(?![\w-])")
    def ensure_reference(self,text,wid,pid,han=None):
        candidates=set(self.terms.get(norm(text),set()))
        if han:candidates |= self.terms.get(norm(han),set())
        if len(candidates)==1:return next(iter(candidates))
        key=wid+'|'+(han or norm(text));ident='person-ref-'+sha(key.encode())[:16]
        if ident not in self.people:
            p=basic_profile(ident,han or text,wid,text if han else None,undivided=not han)
            p['sources'][wid]=self.evidence_source(wid,pid)
            p['notes']=['Source-scoped reference. No identity with a similarly named person elsewhere is asserted.']
            self.people[ident]=p;self.register_entity(p)
        return ident
    def work_id(self,title,wid,pid):
        cand=self.by_work.get(norm(title),set())
        if len(cand)==1:return next(iter(cand))
        ident='work-ref-'+sha((wid+'|'+norm(title)).encode())[:16]
        if ident not in self.works:
            self.works[ident]={'schemaVersion':1,'id':ident,'type':'work','title':title,'attestedTitles':[title],'kind':'work-title-candidate','creators':[],'reviewStatus':'agent-proposed','sources':{wid:self.evidence_source(wid,pid)},'mentions':[],'note':'Source-scoped title candidate. A typographic title is not a fully resolved work/edition identification.'}
            self.entities[ident]={'id':ident,'type':'work','label':title,'display':title,'sources':[wid],'aliases':[]}
        return ident
    def annotate(self,n,wid,pid,subject,language='en'):
        text=n.text();hits=[];offsets=[]
        def walk(x,pos=0,italic=False):
            if isinstance(x,str):return pos+len(x)
            start=pos
            for c in x.children:pos=walk(c,pos,italic or x.tag in {'i','em'})
            if x.tag:offsets.append((start,pos,x,italic))
            return pos
        walk(n)
        # Explicit printed work typography is a recognition signal, not an identity claim.
        for a,b,x,outeritalic in offsets:
            if x.tag not in {'i','em'} or outeritalic:continue
            title=x.text().strip();low=norm(title)
            if low in NOT_WORK or len(title)<4 or not re.search('[A-Za-z\u3400-\u9fff]',title):continue
            if not ((' ' in title and len(title)>7) or ('-' in title and len(title)>6) or re.search(HAN+'{2}',title)):continue
            if re.fullmatch(r'[0-9 /.,–—-]+',title):continue
            ident=self.work_id(title,wid,pid);lo=a+len(x.text())-len(x.text().lstrip());hits.append((lo,lo+len(title),ident,1,'work-title-typography'))
        for a,b,x,italic in offsets:
            if x.tag!='a' or b<=a:continue
            key=article_key(x.attrs.get('href',''));ident=self.article_people.get(key)
            if not ident:continue
            label=x.text().strip();p=self.people[ident]
            terms={norm((p['name'].get('surname') or '')+p['name']['given']),norm(key[len(PREFIX):])}
            terms|={norm(r['value']) for r in p['name'].get('romanizations',[])}
            # A link on 'Macartney (see under Kuo)' is not Kuo's identity.
            if norm(label) not in terms:
                ident=self.ensure_reference(label,wid,pid)
                if not any(a.get('relation')=='mentioned-in' for a in self.people[ident]['accounts']):self.people[ident]['accounts'].append({'source':wid,'relation':'mentioned-in','url':url(key),'passage':pid})
            lo=a+len(x.text())-len(x.text().lstrip());hits.append((lo,lo+len(label),ident,0,'upstream-cross-reference'))
        local=defaultdict(set)
        # Candidate full romanized personal names with explicit Chinese forms.
        pairs=re.compile(r"(?<![\w])([A-ZÀ-Þ][a-zà-ÿ'’ʻ-]{1,18}\s+[A-ZÀ-Þ][a-zà-ÿ'’ʻ]+(?:-[a-zà-ÿ'’ʻ]+){0,3})\s+("+HAN+r'{2,6})(?=[ ,，(（])')
        for m in pairs.finditer(text):
            if any(a<=m.start()<b and self.entities[e]['type']=='work' for a,b,e,_,_ in hits):continue
            ident=self.ensure_reference(m[1],wid,pid,m[2]);enrich_opening(self.people[ident],text[m.start():m.start()+400],wid);local[norm(m[1])].add(ident);local[norm(m[2])].add(ident)
            hits.extend([(m.start(1),m.end(1),ident,2,'romanized-name-with-Han-form'),(m.start(2),m.end(2),ident,2,'romanized-name-with-Han-form')])
        # Repeated full names already attested in the shared catalogue.
        # A shared compiled matcher avoids scanning thousands of names separately.
        for a,b,term in self.name_matcher.find(text):
            ids=self.terms.get(term,set())
            if len(ids)!=1:continue
            if language=='en' and not re.search(HAN,text[a:b]) and text[a].islower():continue
            if text[a].isascii() and a and (text[a-1].isalnum() or text[a-1]=='_'):continue
            if text[b-1].isascii() and b<len(text) and (text[b].isalnum() or text[b] in '_-'):continue
            hits.append((a,b,next(iter(ids)),3,'full-attested-name-match'))
        relevant=[]
        for term,ids in local.items():
            if len(ids)==1:relevant.append((term,next(iter(ids))))
        if subject:
            p=self.people[subject]
            for term in [(p['name'].get('surname') or '')+p['name']['given']]+[r['value'] for r in p['name'].get('romanizations',[])]:
                if term:relevant.append((term,subject))
        for term,ident in relevant:
            pattern=re.escape(term)
            if term[0].isascii() or ' ' in term:pattern=r'(?<![\w])'+pattern+r'(?![\w-])'
            for m in re.finditer(pattern,text,re.I):hits.append((m.start(),m.end(),ident,3,'full-attested-name-match'))
        # Unlinked romanized names receive source-scoped profiles, never guessed dates.
        for m in self.roman_pattern.finditer(text):
            if any(a<=m.start()<b for a,b,_,_,_ in hits):continue
            ident=self.ensure_reference(m[0],wid,pid);hits.append((m.start(),m.end(),ident,4,'romanized-name-candidate'))
        hits.sort(key=lambda x:(x[0],x[3],-(x[1]-x[0])));selected=[];end=-1
        for hit in hits:
            if hit[0]<end:continue
            selected.append(hit);end=hit[1]
        parts=[];cursor=0;ms=[]
        for i,(a,b,ident,priority,origin) in enumerate(selected,1):
            mid=pid+'-n'+str(i).zfill(3);parts +=[fragment(n,cursor,a),f'<span id="{mid}" data-entity="{ident}">'+fragment(n,a,b)+'</span>'];cursor=b
            ms.append({'id':mid,'witness':wid,'passage':pid,'entity':ident,'quote':text[a:b],'status':'proposed','origin':'eccp-round1:'+origin})
        parts.append(fragment(n,cursor,len(text)))
        marked=f'<p id="{pid}">'+''.join(parts)+'</p>'
        if TextIndex(marked).passages[pid]!=text:raise ValueError('Annotation changed wording')
        return marked,ms
    def write_document(self,doc,language='en'):
        wid=doc['wid'];s=self.sources[wid];base=[];working=[];layout=[];ms=[]
        for i,n in enumerate(doc['blocks'],1):
            pid=f'{wid}-{i:03}';baseline=f'<p id="{pid}">'+fragment(n,0,len(n.text()))+'</p>'
            marked,mentions=self.annotate(n,wid,pid,doc['subject'],language)
            base.append(baseline);working.append(marked);ms+=mentions
            layout.append({'passage':pid,'sourceBlock':i,'section':'source-body','characters':len(n.text())})
        text='\n'.join(working)+'\n';baseline='\n'.join(base)+'\n'
        for field,value in [('text',text),('upstream',baseline)]:
            path=self.root/s[field];path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value,encoding='utf-8')
            s['sha256' if field=='text' else 'upstreamSha256']=sha(value.encode())
        s['passageLayout']=layout;self.c['sources'].append(s);self.c['mentions']+=ms
        for m in ms:
            e=self.entities[m['entity']];records=self.people if e['type']=='person' else self.works;r=records[m['entity']]
            r['sources'].setdefault(wid,self.evidence_source(wid,m['passage']))
            # The catalogue holds all occurrence lists; avoid copying tens of thousands per profile.
            if e['type']=='work':
                if m['quote'] not in r['attestedTitles']:r['attestedTitles'].append(m['quote'])
                r.setdefault('mentions',[]).append({'witness':wid,'passage':m['passage'],'mention':m['id'],'quote':m['quote']})
        return len(ms)
    def qsg_matches(self):
        manifest=json.load(open(self.qsg/'manifest.json'));docs=[];candidates=defaultdict(list)
        for row in manifest:
            if row['status']!='downloaded-not-reviewed':continue
            obj=json.load(open(self.qsg/row['path']))['parse'];blocks,whole=reading_blocks(obj['text']['*'],'zh')
            wid='qsg-volume-'+row['title'].split('卷')[-1]
            for i,n in enumerate(blocks,1):
                opening=n.text().strip();m=re.match('('+HAN+'{2,7})[，,](?:字|初名|一名|姓|'+HAN+'{2,6}氏|滿洲|蒙古|漢軍|先世|'+ '|'.join(PROVINCES)+')',opening)
                if m:
                    name=m[1].replace('籓','藩');candidates[name].append((wid,i,opening[:250]))
                m=re.search('諱('+HAN+'{2,6})[，,。]',opening[:250])
                if m and int(row['title'].split('卷')[-1])<=25:candidates[m[1]].append((wid,i,opening[:250]))
            docs.append({'wid':wid,'row':row,'blocks':blocks,'whole':whole,'subject':None,'kind':'qsg-volume','existing':False})
        used=set()
        for p in list(self.people.values()):
            name=(p['name'].get('surname') or '')+p['name']['given'];cs=candidates.get(name,[])
            # Do not silently choose a namesake. Retain multiple openings as candidates.
            if not cs:continue
            for wid,i,opening in cs:
                used.add(wid);match={'person':p['id'],'witness':wid,'passage':f'{wid}-{i:03}','opening':opening,'status':'proposed','method':'biographical-opening-name-match','note':'Opening matched; account identity and boundaries await individual review.'}
                self.qmatches.append(match)
        # Import each matched volume once in full; account links point at openings.
        for doc in docs:
            if doc['wid'] not in used:continue
            wid=doc['wid'];self.sources[wid]=self.source_record(wid,doc['row'],'qsg-volume',None,'zh',doc['blocks'],doc['whole'])
            self.write_document(doc,'zh')
        for m in self.qmatches:
            p=self.people[m['person']];wid=m['witness'];p['sources'][wid]=self.evidence_source(wid,m['passage'])
            p['accounts'].append({'source':wid,'relation':'biographical-account-candidate','readerWitness':wid,'passage':m['passage'],'matchStatus':'proposed','evidence':m['opening']})
            # Registration wording is retained verbatim, without inventing 民籍 or 佐領.
            if re.search('人[。；，]',m['opening'][:130]):
                n=p['name'];reg=n.setdefault('registration',{'attestations':[]});att={'text':m['opening'].split('。')[0]+'。','source':wid,'kind':'biographical-opening','status':'proposed'}
                if att not in reg['attestations']:reg['attestations'].append(att)
                if not n.get('bracket'):
                    match=re.search('(?:'+ '|'.join(PROVINCES)+')('+HAN+'{2,4}?)(?:縣)?人',m['opening'][:90])
                    if match:
                        locality=match[1]
                        if locality not in {'順天','福州','杭州','蘇州','揚州','廣州','惠州','潮州','長沙','常德','岳州','衡州','永州','寶慶','桂林','梧州','太原','大同','平陽','濟南','青州','登州','萊州','開封','河南','西安','漢中','成都','重慶','寧波','紹興','台州','臺州','衢州','溫州','湖州','嘉興','漳州','泉州','建寧','汀州','延平','興化','廬州','安慶','徽州','寧國','池州','鳳陽','九江','饒州','撫州','贛州','南安','吉安','臨江','袁州','武昌','漢陽','黃州','荊州','襄陽','鄖陽','雲南','大理','曲靖','貴陽','遵義'}:
                            n['bracket']={'kind':'county','label':locality,'source':wid,'status':'proposed'}
    def finish(self):
        # Explicit canonical display changes for existing profiles, no source edits.
        for p in self.people.values():
            n=p['name'];n.setdefault('bracket',None);n.setdefault('registration',{'attestations':[]})
            if n.get('clan'):n['bracket']={'kind':'clan','label':n['clan']['label'],'source':n['clan']['source']}
            if n.get('jiguan'):
                label=n['jiguan']['label'];short=label
                for prov in PROVINCES:
                    if short.startswith(prov):short=short[len(prov):];break
                short=re.sub('縣$','',short)
                if re.fullmatch(HAN+'{2,4}',short) and not n.get('clan'):n['bracket']={'kind':'county','label':short,'source':n['jiguan']['source']}
                if not any(a['text']==label for a in n['registration']['attestations']):n['registration']['attestations'].append({'text':label,'source':n['jiguan']['source'],'kind':'previous-record'})
        p=self.people['person-chonghou'];n=p['name'];n['surname']=None;n['given']='崇厚';n['bracket']={'kind':'clan','label':'完顏','source':'eccp'};n['clan']={'label':'完顏','source':'eccp'}
        for ident in list(self.works):
            if not self.works[ident].get('mentions'):
                del self.works[ident];self.entities.pop(ident,None)
        p=self.people['person-chonghou'];p['name']['registration']['attestations'].append({'text':'member of the Wanyen 完顏 clan and of the Manchu Bordered Yellow Banner','source':'eccp','kind':'source-wording'})
        self.c['entities']=list(self.entities.values());dump(self.root/'data/catalog.json',self.c)
        for ident,p in self.people.items():dump(self.root/f'data/people/{ident}.json',p)
        for ident,w in self.works.items():dump(self.root/f'data/works/{ident}.json',w)
        dump(self.root/'data/people/index.json',{'schemaVersion':1,'profiles':[i+'.json' for i in self.people]})
        dump(self.root/'data/works/index.json',{'schemaVersion':1,'works':[i+'.json' for i in self.works]})
        library=[{'source':d['wid'],'title':d['entry'],'person':d['subject'],'kind':d['kind'],'pageid':d['row']['pageid'],'complete':True,'revision':d['row']['revision']} for d in self.documents]
        report={'schemaVersion':1,'entries':library,'counts':{'eccpSources':len(library),**Counter(d['kind'] for d in self.documents),'people':len(self.people),'works':len(self.works),'mentions':len(self.c['mentions']),'qsgOpeningCandidates':len(self.qmatches),'qsgVolumes':len({m['witness'] for m in self.qmatches})},'reviewStatus':'automated-first-pass','limitations':['Full text coverage is separate from annotation recall and identity correctness.','Unlinked names and title references require subsequent editorial review.','QSG opening matches are candidates, not adjudicated identifications.','Unknown CBDB/Geni identifiers, calendar years and registry details are not inferred.']}
        dump(self.root/'data/collections/eccp.json',report);dump(self.root/'data/collections/qsg-concordance.json',{'schemaVersion':1,'matches':self.qmatches})
        dump(self.root/'data/imports/round1/manifest.json',json.load(open(self.raw/'manifest.json')))
        for name in ['inventory.json','eccp-index.response.json','qsg-index.response.json']:
            shutil.copyfile(self.raw/name,self.root/'data/imports/round1'/name)
        print(json.dumps(report['counts'],ensure_ascii=False,indent=2))
    def run(self):
        if (self.root/'data/collections/eccp.json').exists():raise ValueError('Round one already imported; use reviewed changes, not a destructive rebuild')
        self.prepare()
        for i,doc in enumerate(self.documents,1):
            if not doc['existing']:self.write_document(doc)
            if i%100==0:print('ECCP',i,'/',len(self.documents),flush=True)
        self.qsg_matches();self.finish()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--qsg',type=Path,required=True);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();Importer(a.root,a.raw,a.qsg).run()
