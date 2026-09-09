"""One-time, hash-checked integration of the family renderer; never edits corpus data."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[2]
HASHES={
 'assets/reader-context.js':('b9866473871ff12a1736eef538c2d48b8e9370442dd80d5d2a1a7e9043da3ca0','c29df44bf8b6359daaa655b8053219760da6e0da683fd99a90a3ff77109cedc2'),
 'assets/i18n.js':('e872ae9d7c85c6bbbb970d5cc676da82bd9f8e87d9e76c87d51aaf849ddca995','812029ddf1d33568083a5dbb73893fb74a413d6bfd141ce34a89cd8d2a45b668'),
 'index.html':('b0491f6062882a373b1ca373584cb8fff67df61088b157fd5b713ae9edfb88e8','d7d202669f8061390b956f297a14e6cc519df28879f6caa5a5a7c0df0c537abb')}

def migrate(file,s):
    if file=='index.html':return s.replace('<link rel="stylesheet" href="assets/i18n.css">','<link rel="stylesheet" href="assets/i18n.css">\n<link rel="stylesheet" href="assets/reading-layout.css">')
    if file=='assets/i18n.js':return s.replace("import chinese from './locale-zh.js';", "import baseChinese from './locale-zh.js';\nimport familyChinese from './family-locale.js';\nconst chinese = {...baseChinese, ...familyChinese};")
    s=s.replace("import {orderedPeople, familyEdges, jurisdictionChain,", "import {createFamilyTimeline} from './family-timeline.js';\nimport {familyHierarchy} from './family-layout.js';\nimport {jurisdictionChain,")
    s=s.replace('let current=null, previousOrder=[], grouped=true, selectedPerson=null, pendingJump=null;', 'let current=null, selectedPerson=null, pendingJump=null;')
    s=s.replace('let chosenJurisdiction=null, lastPassage=null, frame=0, animation=0;\n  const rows=new Map(), positions=new Map();','let chosenJurisdiction=null, lastPassage=null, frame=0;')
    a=s.index('  const time=document.createElement(');b=s.index('\n  const panel=',a)
    s=s[:a]+'''  const time=document.createElement('div');time.className='context-timeline';
  $('timeline').before(time);$('timeline').style.display='none';
  const familyTimeline=createFamilyTimeline({host:time,catalog,people,passageButton,onEvidence:evidence,
    onSelect(id){selectedPerson=id;$('trajectory-person').value=id;paintMap();report('Trajectory: {name}. Only documented movements are shown.',{name:shortName(people.get(id))});}});
'''+s[b:]
    a=s.index('  function updateTimeline(){');b=s.index('  function refresh(){',a)
    s=s[:a]+"  function updateTimeline(){if(current)familyTimeline.update(current);}\n"+s[b:]
    s=s.replace('if(sourceChanged){previousOrder=[];selectedPerson=source.subject;}','if(sourceChanged){selectedPerson=source.subject;}')
    return s.replace("const ids=[...new Set([source.subject,...inNode($('reader'))", "const familyIds=familyHierarchy(source.subject,catalog.relations,[...people.keys()]).members.map(m=>m.id);\n    const ids=[...new Set([source.subject,...familyIds,...inNode($('reader'))")

if __name__=='__main__':
    output={}
    for file,(before,after) in HASHES.items():
        raw=(ROOT/file).read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest==after:continue
        if digest!=before:raise ValueError(f'{file}: source changed; review migration before proceeding')
        result=migrate(file,raw.decode()).encode()
        if hashlib.sha256(result).hexdigest()!=after:raise ValueError(f'{file}: integration did not produce tested bytes')
        output[file]=result
    for file,raw in output.items():(ROOT/file).write_bytes(raw)
    print(f'Integrated {len(output)} files; no corpus changes')
