"""Render cropped, attributed CHGIS map-label illustrations, never source vectors.

Run only for map preparation (geopandas/Pillow required). Normal builds are offline.
The existing source checksums pin the labels to precisely the boundary snapshots.
"""
from pathlib import Path
import hashlib, io, json, subprocess, tempfile, urllib.request, zipfile
import geopandas as gpd
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import box, Point

ROOT = Path(__file__).resolve().parents[1]

def run(root=ROOT):
    manifest_path = root/'data/reference-maps.json'
    manifest = json.loads(manifest_path.read_text())
    bbox = manifest['bbox']; width, height = 3000, 2200
    crop = box(*bbox)
    out = root/'assets/maps'; out.mkdir(parents=True, exist_ok=True)
    font_path = subprocess.check_output(['fc-match', 'Noto Sans CJK TC', '-f', '%{file}'], text=True)
    labels = []
    def pixel(x, y):
        return ((x-bbox[0])/(bbox[2]-bbox[0])*width, (bbox[3]-y)/(bbox[3]-bbox[1])*height)
    def geographic(x, y):
        return Point(bbox[0]+x/width*(bbox[2]-bbox[0]), bbox[3]-y/height*(bbox[3]-bbox[1]))
    def field(row, keys):
        for key in keys:
            value = str(row.get(key, '')).strip()
            if value and value not in ('None', 'nan', '<NA>'):
                return value
        return ''
    with tempfile.TemporaryDirectory() as td:
        for layer in manifest['layers']:
            request = urllib.request.Request(layer['sourceURL'], headers={'User-Agent': 'Ren-Wen academic map labels; github.com/liuyao12/ren-wen'})
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read(60000001)
            assert len(raw) <= 60000000
            assert hashlib.sha256(raw).hexdigest() == layer['sourceSha256'], 'Boundary source changed; review before rebuilding labels.'
            directory = Path(td)/str(layer['sourceFileId']); directory.mkdir()
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                for name in archive.namelist():
                    (directory/name).resolve().relative_to(directory.resolve())
                archive.extractall(directory)
            shp = next(directory.rglob('*.shp'))
            frame = gpd.read_file(shp, encoding='gb18030' if layer['year']==1820 else 'utf-8')
            assert frame.crs is not None, 'Unknown CRS'
            frame = frame.to_crs('EPSG:4326')
            candidates = []
            for _, row in frame[frame.intersects(crop)].iterrows():
                geometry = row.geometry
                if not geometry.is_valid:
                    geometry = geometry.buffer(0)
                clipped = geometry.intersection(crop)
                if clipped.is_empty: continue
                name = field(row, ['NAME_FT', 'NAME_CH'])
                if not name: continue
                kind = field(row, ['TYPE_CH'])
                # Only append an explicitly supplied administrative type.
                if kind in ('省','府','州','縣','县','廳','厅') and not name.endswith(('省','府','州','縣','县','廳','厅')):
                    name += {'县':'縣','厅':'廳'}.get(kind, kind)
                p = clipped.representative_point()
                candidates.append((clipped.area, name, pixel(p.x,p.y), clipped))
            # The old province illustration already contained baked-in labels.
            # Replace it with identical linework, so each name is drawn only once.
            if layer['level']=='province':
                outlines=Image.new('RGBA',(width,height)); pen=ImageDraw.Draw(outlines)
                for _,row in frame[frame.intersects(crop)].iterrows():
                    geometry=row.geometry
                    if not geometry.is_valid: geometry=geometry.buffer(0)
                    edge=geometry.intersection(crop).boundary.difference(crop.boundary.buffer(.00001))
                    def lines(g):
                        if g.geom_type=='LineString': yield g
                        else:
                            for child in getattr(g,'geoms',[]): yield from lines(child)
                    for line in lines(edge): pen.line([pixel(x,y) for x,y,*_ in line.coords],fill=(100,74,57,255),width=5)
                target=root/layer['file'];outlines.save(target,optimize=True)
                layer['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
                layer['changes']+=' Province names moved to separately switchable label illustrations.'
            variants = {'province': [('overview', 70, 0, 1000)],
                        'prefecture': [('regional', 52, 6, 1000), ('detail', 27, 0, 6)],
                        'county': [('regional', 30, 3, 1000), ('detail', 15, 0, 3)]}[layer['level']]
            for variant, font_size, minimum, maximum in variants:
                image = Image.new('RGBA', (width,height)); draw = ImageDraw.Draw(image)
                font = ImageFont.truetype(font_path, font_size)
                occupied = []; placed = 0
                for _, name, (cx,cy), geometry in sorted(candidates, key=lambda x: (-x[0],x[1])):
                    for dx,dy in [(0,0),(0,-font_size),(0,font_size),(-font_size,0),(font_size,0)]:
                        x,y = cx+dx,cy+dy
                        if not geometry.covers(geographic(x,y)): continue
                        rect = draw.textbbox((x,y),name,font=font,anchor='mm',stroke_width=2)
                        if rect[0]<0 or rect[1]<0 or rect[2]>width or rect[3]>height: continue
                        if any(not(rect[2]+2<a or rect[0]-2>c or rect[3]+2<b or rect[1]-2>d) for a,b,c,d in occupied): continue
                        draw.text((x,y),name,font=font,anchor='mm',fill=(39,63,56,255),stroke_width=2,stroke_fill=(255,253,243,250))
                        occupied.append(rect); placed+=1; break
                assert placed>0, 'No readable labels produced'
                filename=f'chgis-{layer["year"]}-{layer["level"]}-names-{variant}.png'
                image.save(out/filename, optimize=True)
                labels.append({'id':filename[:-4], 'file':'assets/maps/'+filename,
                    'year':layer['year'],'level':layer['level'],'variant':variant,
                    'minViewWidth':minimum,'maxViewWidth':maximum,'bbox':bbox,
                    'labelCount':placed,'candidateCount':len(candidates),
                    'sourceFileId':layer['sourceFileId'],'sourceURL':layer['sourceURL'],
                    'sourceSha256':layer['sourceSha256'],
                    'sha256':hashlib.sha256((out/filename).read_bytes()).hexdigest(),
                    'changes':'Chinese labels from NAME_FT (fallback NAME_CH), at interior cartographic positions, not county seats. Cropped to the same academic map region; collision filtering and scale-dependent type sizes. No vector geometry or gazetteer table distributed.'})
                print(layer['year'],layer['level'],variant,placed,'/',len(candidates))
    manifest['labelLayers']=labels
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return labels

if __name__ == '__main__':
    run()
