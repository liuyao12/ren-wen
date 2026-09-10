"""Keep compact naming separate from source-attributed full registration wording."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def apply(root=ROOT):
    geo=json.loads((root/'data/geography.json').read_text());count=0
    for path in (root/'data/people').glob('person-*.json'):
        p=json.loads(path.read_text());n=p['name'];reg=n.setdefault('registration',{'attestations':[]});br=n.get('bracket') or {}
        # Only existing source-linked geographical records are used here.
        if br.get('kind')=='county' and br['label'] in {'湘鄉','上海'}:
            key='qsg68' if br['label']=='湘鄉' else 'qsg58';source=geo['sources'][key];citation='registry-geography'
            p['sources'][citation]={**source,'locator':'長沙府下湘鄉' if key=='qsg68' else '松江府下上海'}
            reg.update(administrativeLabel='湖南長沙府湘鄉縣' if key=='qsg68' else '江蘇松江府上海縣',administrativeSource=citation,kind='administrative-hierarchy',registrationCategory=None,company=None,note='Administrative path assembled from the cited geography and native-place record. 民籍 and other registration categories are not stated.')
        if p['id']=='person-chonghou':
            a=next((a for a in p['accounts'] if a.get('readerWitness')=='qsg-volume-446'),None)
            if a:
                reg.update(administrativeLabel='內務府鑲黃旗',administrativeSource=a['source'],kind='banner-registration',company=None,note='QSG gives 內務府鑲黃旗人; the company (佐領) is not stated. ECCP wording is retained separately.')
        path.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n');count+=1
    return count
if __name__=='__main__':print(json.dumps({'profiles':apply()}))
