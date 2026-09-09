import sys,json,shutil,hashlib
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R))
from scripts.eccp_batch import Tree,nodes,clean,fragment,annotate
from scripts.eccp_compile import dump
from scripts.renwen import TextIndex
c=json.loads((R/'data/catalog.json').read_text());s=next(s for s in c['sources'] if s['id']=='qsg')
inputs=R/'build/text-map-inputs/reference-maps'
raw=(inputs/'qsg-446.response.json').read_bytes();resp=json.loads(raw)['parse']
ps=[n for n in nodes(Tree(resp['text']['*']).root) if n.tag=='p'];a=next(i for i,p in enumerate(ps) if p.text().strip().startswith('曾紀澤，'));last=next(i for i in range(a+1,len(ps)) if ps[i].text().strip().startswith('薛福成，'));selected=ps[a:last];assert len(selected)==4
n=clean(selected[1]);txt=n.text().strip();n=Tree(fragment(n,len(n.text())-len(n.text().lstrip()),len(n.text().rstrip()))).root
rules=[{'entity':person,'terms':terms,'witness':'qsg','note':'Explicit or contextually resolved person reference in the restored memorial.'} for person,terms in [('person-zeng-jize',['紀澤']),('person-chonghou',['崇厚']),('person-zuo-zongtang',['左宗棠'])]]
pid='qsg-02';marked,ms=annotate(n,rules,pid,[])
for m in ms:m['origin']='qsg-restored-memorial'
for kind,content in [('texts',marked),('upstream',f'<p id="qsg-02">'+fragment(n,0,len(n.text()))+'</p>')]:
 p=R/f'data/{kind}/qsg.html';t=p.read_text();assert 'id="qsg-02"' not in t;t=t.replace('<p id="qsg-03">',content+'\n<p id="qsg-03">');p.write_text(t)
 s['sha256' if kind=='texts' else 'upstreamSha256']=hashlib.sha256(p.read_bytes()).hexdigest()
idx=TextIndex((R/s['text']).read_text());compact=lambda t:''.join(t.split())
assert compact(''.join(idx.passages.values()))==compact(''.join(clean(p).text() for p in selected))
folder=R/'data/imports/qsg-zeng-jize';folder.mkdir(parents=True,exist_ok=True);(folder/'response.json').write_bytes(raw);shutil.copy(inputs/'qsg-manifest.json',folder/'manifest.json')
s.update(complete=True,extent='Complete 曾紀澤 account in 卷446, including the previously omitted memorial; not the entire multi-person volume.',importMethod='Original paragraph IDs and annotations preserved; missing qsg-02 restored from the retained full-volume MediaWiki response.',rawResponse='data/imports/qsg-zeng-jize/response.json',rawSha256=hashlib.sha256(raw).hexdigest(),completeness={'method':'bounded-biography-versus-source-paragraphs','paragraphs':4,'startsWith':'曾紀澤，字劼剛','nextBiographyStartsWith':'薛福成，字叔耘','normalizedBodySha256':hashlib.sha256(compact(''.join(idx.passages.values())).encode()).hexdigest()})
c['mentions']+=ms;dump(R/'data/catalog.json',c)
for m in ms:
 p=R/f'data/people/{m["entity"]}.json'
 if p.exists():
  q=json.loads(p.read_text());q.setdefault('mentions',[]).append({k:m[k] for k in ['witness','passage','quote']}|{'mention':m['id']});dump(p,q)
units=[];occ=[]
for source in c['sources']:
 wid=source['id'];pidx=TextIndex((R/source['text']).read_text());uid='text-'+wid
 units.append({'id':uid,'kind':'biography','title':source['shortTitle'],'work':source['work'],'subject':source['subject'],'reviewStatus':'agent-proposed'})
 occ.append({'id':'occ-'+wid,'unit':uid,'witness':wid,'role':'complete-reading','readingType':'source-reading','selectors':[{'passage':k,'start':0,'end':len(v),'exact':v} for k,v in pidx.passages.items()],'sourceSha256':source['sha256']})
text=idx.passages['qsg-02'];start=text.index('「')+1;end=text.rindex('」')
units.append({'id':'text-zeng-jize-yili-memorial','kind':'memorial','title':'曾紀澤論伊犁交涉疏（《清史稿》引文）','titleStatus':'editorial-descriptive','author':'person-zeng-jize','reviewStatus':'agent-proposed','note':'編者描述性題名，不聲稱原疏即以此為題。現只登記《清史稿》所引讀法；將來可連接原疏及其他引文，各保留原文，不自動合併。'})
occ.append({'id':'occ-qsg-yili-memorial','unit':'text-zeng-jize-yili-memorial','witness':'qsg','container':'occ-qsg','role':'quotation','readingType':'quoted-reading','selectors':[{'passage':'qsg-02','start':start,'end':end,'exact':text[start:end]}],'sourceSha256':s['sha256'],'attributionExpression':'紀澤乃疏言','note':'引文仍完整保留在本傳；本記錄不是第二個獨立史料證據。'})
z=next(s for s in c['sources'] if s['id']=='eccp-zeng-guofan');zt=TextIndex((R/z['text']).read_text()).passages
units.append({'id':'text-eccp-zeng-guofan-bibliography','kind':'bibliography','title':'ECCP 曾國藩傳 · 參考書目','parentUnit':'text-eccp-zeng-guofan','reviewStatus':'agent-proposed'})
occ.append({'id':'occ-eccp-zeng-guofan-bibliography','unit':'text-eccp-zeng-guofan-bibliography','witness':z['id'],'container':'occ-'+z['id'],'role':'section','readingType':'source-reading','selectors':[{'passage':'eccp-zeng-guofan-16','start':0,'end':len(zt['eccp-zeng-guofan-16']),'exact':zt['eccp-zeng-guofan-16']}],'sourceSha256':z['sha256']})
dump(R/'data/text-units.json',{'schemaVersion':1,'units':units,'occurrences':occ,'relations':[],'note':'Units identify texts; occurrences preserve each witness reading. Containers are occurrence-specific; identical words are not sufficient evidence of quotation or textual dependence.'})
print(len(units),len(occ),len(text[start:end]))
