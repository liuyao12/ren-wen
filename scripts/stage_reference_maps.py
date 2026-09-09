"""Build cropped educational reference images from CHGIS; never publish source layers.

File-level EULA sections 4/5: portions and attributed map images for academic
publications; no republication of entire datasets. Deliberately clip to the
middle/lower Yangtze corridor. The full input ZIPs stay in a temporary directory.
Requires geopandas and Pillow only for this offline build, not for the webapp.
"""
from pathlib import Path
import tempfile, urllib.request, urllib.parse, json, hashlib, zipfile, subprocess
from datetime import datetime, timezone
import geopandas as gpd
from PIL import Image, ImageDraw, ImageFont

OUT=Path('build/reference-maps');OUT.mkdir(parents=True,exist_ok=True)
BBOX=[108,24,123,35]
WIDTH,HEIGHT=3000,2200
CREDIT='CHGIS Version 6. © Fairbank Center for Chinese Studies and the Institute for Chinese Historical Geography at Fudan University, Dec 2016.'
UA='Ren-Wen academic map illustration (https://github.com/liuyao12/ren-wen)'
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=90) as r:return r.read(60000000)
def point(x,y):return ((x-BBOX[0])/(BBOX[2]-BBOX[0])*WIDTH,(BBOX[3]-y)/(BBOX[3]-BBOX[1])*HEIGHT)
def polygons(g):
    if g.geom_type=='Polygon':return [g]
    if hasattr(g,'geoms'):return [p for c in g.geoms for p in polygons(c)]
    return []
manifest={'schemaVersion':1,'kind':'cropped-historical-map-images','bbox':BBOX,'width':WIDTH,'height':HEIGHT,'attribution':CREDIT,'termsURL':'https://dataverse.harvard.edu/api/access/datafile/2966703','termsNote':'Cropped academic map images under CHGIS EULA §4. Source vector datasets are not redistributed. Not licensed as Ren-Wen software.','scope':'湘鄂贛皖蘇浙及鄰近地區局部；非全國覆蓋。','layers':[]}
eula=fetch(manifest['termsURL']);(OUT/'CHGIS-V6-EULA.txt').write_bytes(eula)
assert b'(4) citation' in eula and b'digital images' in eula
fontpath=subprocess.check_output(['fc-match','Noto Sans CJK SC','-f','%{file}']).decode()
font=ImageFont.truetype(fontpath,35)
from shapely.geometry import box
crop=box(*BBOX)
with tempfile.TemporaryDirectory() as td:
    for year,level,fileid,encoding in [(1820,'province',2966705,'gb18030'),(1820,'prefecture',2966700,'gb18030'),(1911,'province',2966688,'utf-8'),(1911,'prefecture',2966689,'utf-8'),(1911,'county',2966692,'utf-8')]:
        url=f'https://dataverse.harvard.edu/api/access/datafile/{fileid}';raw=fetch(url)
        zipfile.ZipFile(__import__('io').BytesIO(raw)).extractall(Path(td)/str(fileid))
        shp=next((Path(td)/str(fileid)).rglob('*.shp'));df=gpd.read_file(shp,encoding=encoding)
        if df.crs is None:raise ValueError('Missing CRS; do not guess')
        df=df.to_crs('EPSG:4326');df=df[df.intersects(crop)]
        image=Image.new('RGBA',(WIDTH,HEIGHT),(0,0,0,0));d=ImageDraw.Draw(image)
        line={'province':(100,74,57,255),'prefecture':(103,114,93,220),'county':(107,122,122,210)}[level]
        width={'province':5,'prefecture':3,'county':2}[level]
        labels=[]
        for _,row in df.iterrows():
            g=row.geometry
            if not g.is_valid:g=g.buffer(0)
            g=g.intersection(crop)
            for poly in polygons(g):
                # Clip original boundary lines instead of drawing artificial crop-box borders.
                edge=poly.boundary.difference(crop.boundary.buffer(.00001))
                lines=[edge] if edge.geom_type=='LineString' else list(getattr(edge,'geoms',[]))
                for ln in lines:
                    if ln.geom_type=='LineString':d.line([point(x,y) for x,y,*_ in ln.coords],fill=line,width=width)
            if level=='province' and not g.is_empty:
                name=next((str(row[k]) for k in ['NAME_CH','NAME_CHN','NAME','name_ch'] if k in row and str(row[k]) not in ['None','nan','']),None)
                if name:
                    q=g.representative_point();labels.append((point(q.x,q.y),name))
        for xy,name in labels:d.text(xy,name,font=font,anchor='mm',fill=(71,59,50,255),stroke_width=3,stroke_fill=(249,247,238,240))
        name=f'chgis-{year}-{level}-yangtze.png';image.save(OUT/name,optimize=True)
        manifest['layers'].append({'id':f'chgis-{year}-{level}-yangtze','year':year,'level':level,'file':'assets/maps/'+name,'bbox':BBOX,'intersectingFeatures':len(df),'sourceFileId':fileid,'sourceURL':url,'sourceSha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest(),'retrieved':datetime.now(timezone.utc).isoformat(),'changes':'Reprojected to WGS84 lon/lat; cropped to 108–123E, 24–35N; rendered as transparent raster linework. Polygon outlines are map illustrations, not interactive source geometries.','fieldsInspected':list(df.columns)})
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# The pre-existing Qing-shi-gao excerpt omitted a memorial. Preserve the source
# response so the complete biography can be restored and its quotation modeled.
params=urllib.parse.urlencode({'action':'parse','page':'清史稿/卷446','prop':'text|wikitext|revid','format':'json','maxlag':5})
url='https://zh.wikisource.org/w/api.php?'+params
raw=fetch(url);(OUT/'qsg-446.response.json').write_bytes(raw)
(OUT/'qsg-manifest.json').write_text(json.dumps({'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'retrieved':datetime.now(timezone.utc).isoformat()},indent=2)+'\n')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
