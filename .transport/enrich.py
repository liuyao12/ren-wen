import json,re
from pathlib import Path
R=Path.cwd();d=R/'data/imports/eccp-zeng-guofan';rows=json.loads((d/'reference-openings.json').read_text());spec=json.loads((R/'data/editorial/eccp-zeng-guofan.json').read_text());byentry={p.get('entry'):p for p in spec['people']};c=json.loads((R/'data/catalog.json').read_text());entities={e['id']:e for e in c['entities']}
checked={'Chang Yü-chao':'張裕釗','Chi-êr-hang-a':'吉爾杭阿','Fêng Kuei-fên':'馮桂芬','Hsiang Jung':'向榮',"Hsüeh Fu-ch'êng":'薛福成','Hu Lin-i':'胡林翼',"Hung Hsiu-ch'üan":'洪秀全','Jung Hung':'容閎','Ku Yen-wu':'顧炎武','Kuan-wên':'官文',"Li Hsiu-ch'êng":'李秀成','Li Hsü-pin':'李續賓',"Li Shu-ch'ang":'黎庶昌','Li Yüan-tu':'李元度','Lo Tsê-nan':'羅澤南','Ma Hsin-i':'馬新貽',"Pao Ch'ao":'鮑超',"Shih Ta-k'ai":'石達開',"T'a-ch'i-pu":'塔齊布','Wang Shih-to':'汪士鐸','Yü Yüeh':'俞樾'}
for row in rows:
 entry=row['title'].split('/')[-1]
 if entry not in checked or entry not in byentry or not row.get('opening'):continue
 rule=byentry[entry];fp=R/f'data/people/{rule["id"]}.json';p=json.loads(fp.read_text());n=p['name'];old=(n['surname']or'')+n['given']
 if re.fullmatch('[\u3400-\u9fff]+',old):continue
 label=checked[entry];opening=row['opening'];assert label in opening[:80]
 key='eccp-heading';p['sources'][key]={'title':'ECCP · '+entry,'url':row['url'],'locator':'Preserved source opening, revision '+str(row['revision']),'access':'source-extracted-opening','attribution':'ECCP contributors; Arthur W. Hummel, editor; Wikisource contributors'}
 n['surname']=None if rule.get('undivided') else label[0];n['given']=label if n['surname'] is None else label[1:];n['source']=key
 header=opening.split('),')[0] if '),' in opening else opening[:130]
 for kind,prefix in [('zi','T'),('hao','H')]:
  m=re.search(r'\b'+prefix+r'\.\s*([\u3400-\u9fff]+)',header)
  if m and not n[kind]:n[kind]=[{'value':m[1],'source':key}]
 if not n['parenthetical']:
  for kind in ['zi','hao']:
   if n[kind]:n['parenthetical']={'kind':kind,'value':n[kind][0]['value']};break
 if not p['life'].get('westernYears'):
  match=re.search(r'(1\d{3})\s*[–—-]\s*(1\d{3})',opening[:210])
  if match and ' or ' not in opening[:210]:
   p['life']['westernYears']=[{'event':endpoint,'calendar':'gregorian','value':int(y),'source':key,'status':'source-reported'} for endpoint,y in zip(['birth','death'],match.groups())]
 p['notes'].append('Chinese heading checked against the preserved ECCP opening. The full referenced biography is not imported by this operation.')
 fp.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n');entities[p['id']]['label']=label
for child,parent,pid in [('person-zeng-guofan','person-zeng-linshu','01'),('person-zeng-linshu','person-zeng-yuping','01'),('person-zeng-jihong','person-zeng-guofan','15'),('person-zeng-jijing','person-zeng-guofan','15'),('person-zeng-jiyao','person-zeng-guofan','15'),('person-zeng-jichen','person-zeng-guofan','15'),('person-zeng-jifen','person-zeng-guofan','15')]:
 c['relations'].append({'id':'r-'+child.removeprefix('person-')+'-child-of-'+parent.removeprefix('person-'),'subject':child,'predicate':'child-of','object':parent,'evidence':[{'witness':'eccp-zeng-guofan','passage':'eccp-zeng-guofan-'+pid}],'status':'proposed'})
(R/'data/catalog.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
