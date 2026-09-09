"""One-time checked assembly. No main-branch writes and no unverified source downloads."""
from pathlib import Path
import base64,gzip,hashlib,json,subprocess,sys,zipfile,shutil
R=Path.cwd();sys.path.insert(0,str(R));stage=R/'build/text-map-inputs';stage.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
# Preserve exact tested code; all templates are read before any output is written.
encoded=''.join((R/f'.transport/text-map-code-{n:02}.b64').read_text().strip() for n in range(1,4))
# One known transcription error in the temporary transport. Full checksum remains mandatory.
encoded=encoded.replace('KG3+y22mHXiejQ','KG3+y22mHXiezQ')
compressed=base64.b64decode(encoded,validate=True)
assert sha(compressed)=='b22bb1da83ae7ca97aacd1c4418e454a40a2d215f57a02a43cbef6a450753530','Code transport mismatch'
packet=json.loads(gzip.decompress(compressed));assert packet['base']=='c587c0849b223be6cddda6f1b8bad62b49d039dc'
def target(name):
 p=(R/name).resolve()
 assert p.is_relative_to(R) and not name.startswith(('.git/','build/')),'Unsafe output'
 return p
files=packet['files'];templates={}
for name,r in files.items():
 p=target(name);assert (sha(p.read_bytes()) if p.exists() else None)==r['before'],'Base differs: '+name
 if 'template' in r:
  raw=target(r['template']).read_bytes();assert sha(raw)==r['templateSha']
  templates[r['template']]=raw.decode().splitlines(keepends=True)
for name,r in files.items():
 if 'text' in r:raw=r['text'].encode()
 else:
  old=templates[r['template']];last=0;parts=[]
  for start,end,text in r['edits']:
   assert 0<=last<=start<=end<=len(old);parts.extend(old[last:start]);parts.append(text);last=end
  parts.extend(old[last:]);raw=''.join(parts).encode()
 assert sha(raw)==r['after'],'Reconstructed code differs: '+name
 p=target(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
archives={}
def member(aid,name):
 assert aid in {10086515761,10086649239,10086816787} and '/' not in name and '\\' not in name
 if aid not in archives:
  p=stage/f'{aid}.zip'
  with p.open('wb') as f:subprocess.run(['gh','api',f'repos/liuyao12/ren-wen/actions/artifacts/{aid}/zip'],stdout=f,check=True)
  archives[aid]=zipfile.ZipFile(p)
 info=archives[aid].getinfo(name);assert info.file_size<8_000_000
 return archives[aid].read(name)
folder=stage/'zeng';folder.mkdir(exist_ok=True)
raw=member(10086515761,'eccp-zeng-guofan.txt');assert sha(raw)=='1db4a6a4ebc6cf5776bc03237d3b81edd2afb7c59cdd7358f255d99d62e2a0fc'
(folder/'response.json').write_bytes(raw)
meta={'id':'eccp-zeng-guofan','url':'https://en.wikisource.org/w/api.php?action=parse&page=Eminent+Chinese+of+the+Ch%27ing+Period%2FTs%C3%AAng+Kuo-fan&prop=text%7Cwikitext%7Crevid&format=json&maxlag=5','retrieved':'2026-09-09T03:02:50.686820+00:00','sha256':sha(raw),'bytes':len(raw)}
(folder/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
subprocess.run([sys.executable,'.transport/prepare_spec.py'],check=True)
from scripts.import_entry import import_entry
report=import_entry(R/'data/editorial/eccp-zeng-guofan.json',folder/'response.json',folder/'manifest.json',R)
assert report['newMentions']==228
(R/'data/imports/eccp-zeng-guofan/reference-openings.json').write_bytes(member(10086816787,'reference-openings.json'))
subprocess.run([sys.executable,'.transport/enrich.py'],check=True)
# Restore the complete QSG account and quotation hierarchy from a fixed source response.
refs=stage/'reference-maps';refs.mkdir(exist_ok=True)
for name in ['qsg-446.response.json','qsg-manifest.json']:(refs/name).write_bytes(member(10086649239,name))
qmeta=json.loads((refs/'qsg-manifest.json').read_text());assert sha((refs/'qsg-446.response.json').read_bytes())==qmeta['sha256']
subprocess.run([sys.executable,'.transport/restore.py'],check=True)
# Cropped academic map illustrations only. No source vector archive is republished.
manifest=json.loads(member(10086649239,'manifest.json'));manifest['defaultYear']=1911
maps=R/'assets/maps';maps.mkdir(parents=True,exist_ok=True)
(maps/'CHGIS-V6-EULA.txt').write_bytes(member(10086649239,'CHGIS-V6-EULA.txt'))
for layer in manifest['layers']:
 raw=member(10086649239,Path(layer['file']).name);assert sha(raw)==layer['sha256']
 target(layer['file']).write_bytes(raw)
(R/'data/reference-maps.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
c=json.loads((R/'data/catalog.json').read_text());c.update(defaultWitness='eccp-zeng-guofan',defaultPerson='person-zeng-guofan')
(R/'data/catalog.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
p=R/'data/people/person-zeng-guofan.json';d=json.loads(p.read_text())
d['externalIds']['cbdb']={'id':'34344','url':'https://cbdb.fas.harvard.edu/cbdbapi/person.php?id=0034344','status':'matched','source':'dila-identity','checked':'2026-09-09','method':'authority-cross-reference','evidence':'DILA A007457 曾國藩 explicitly maps to CBDB 0034344; name, aliases 伯涵/滌生 and 1811–1872 dates match the ECCP identity. CBDB bulk data is not copied.'}
d['externalIds']['geni']={'id':None,'status':'unresolved','checked':'2026-09-09','note':'Public search did not yield a verified numeric profile ID; do not guess.'}
d['sources']['dila-identity']={'title':'DILA 人名規範 · A007457 曾國藩','url':'https://authority.dila.edu.tw/person/search.php?aid=7457','locator':'Explicit SameAs CBDB link to person 0034344; identity and dates match 曾國藩, 1811–1872.','access':'full-text','attribution':'DILA Authority Database'}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
for name,r in files.items():assert sha(target(name).read_bytes())==r['after'],'Final code hash differs: '+name
summary={'codeFilesVerified':len(files),'entry':report,'files':{str(p.relative_to(R)):sha(p.read_bytes()) for base in ['data','assets'] for p in (R/base).rglob('*') if p.is_file()}}
(R/'build/text-map-checksums.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'codeFilesVerified':len(files),'newMentions':report['newMentions']},indent=2))
