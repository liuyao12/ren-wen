"""DOM tests with exact local fixtures; use browser_live.py for the published site."""
from pathlib import Path
import base64,json,re,shutil,os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
modules={}
def uri(mime,raw):return 'data:'+mime+';base64,'+base64.b64encode(raw).decode()
land=uri('image/svg+xml',(ROOT/'assets/land.svg').read_bytes())
images={str(p.relative_to(ROOT)):uri('image/png',p.read_bytes()) for p in (ROOT/'assets/maps').glob('*.png')}
def module(path):
 path=path.resolve()
 if path in modules:return modules[path]
 text=path.read_text().replace('assets/land.svg',land).replace('href:layer.file,','href:window.__mapImages[layer.file],')
 text=re.sub(r"from\s+(['\"])(\./[^'\"]+)\1",lambda m:'from '+json.dumps(module(path.parent/m[2])),text)
 modules[path]=uri('text/javascript',text.encode());return modules[path]
files={str(p.relative_to(ROOT)):p.read_text() for p in (ROOT/'data').rglob('*') if p.is_file() and p.suffix in ['.json','.html']}
def load(page,filename):
 html=(ROOT/filename).read_text();entries=re.findall(r'<script type="module" src="([^"]+)"',html)
 html=re.sub(r'<script type="module"[^>]*></script>','',html)
 html=re.sub(r'<link rel="stylesheet" href="([^"]+)">',lambda m:'<style>'+(ROOT/m[1]).read_text()+'</style>',html).replace('assets/land.svg',land)
 page.set_content(html)
 page.evaluate('''({files,images})=>{const store=new Map();Object.defineProperty(window,'localStorage',{value:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)}});window.__mapImages=images;window.fetch=async path=>new Response(files[String(path)],{status:Object.hasOwn(files,String(path))?200:404});}''',{'files':files,'images':images})
 for e in entries:page.add_script_tag(type='module',content='import '+json.dumps(module(ROOT/e)))
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,executable_path=os.environ.get('BROWSER_EXECUTABLE') or shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1500,'height':1000},reduced_motion='reduce');errors=[];page.set_default_timeout(10000);page.on('pageerror',lambda e:errors.append(str(e)))
 load(page,'index.html');page.wait_for_selector('#eccp-zeng-guofan-01');page.wait_for_selector('#historic-map');page.wait_for_timeout(500)
 assert page.locator('#reader p[id]').count()==17
 assert page.locator('#reader p[id]').last.inner_text()=='Têng Ssŭ-yü'
 assert page.locator('#reader a[data-work-link]').count()>30
 m=page.locator('#historic-map');before=m.get_attribute('viewBox');box=m.bounding_box();x=box['x']+box['width']*.5;y=box['y']+box['height']*.45
 page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+45,y+20,steps=6);page.mouse.up();assert m.get_attribute('viewBox')!=before
 assert page.locator('[data-reference-year="1911"][data-reference-level="province"]').get_attribute('visibility')=='visible'
 for _ in range(4):page.locator('#context-zoom-in').click()
 assert page.locator('[data-reference-year="1911"][data-reference-level="county"]').get_attribute('visibility')=='visible'
 page.screenshot(path='/mnt/data/ren-wen-county-map.png')
 page.locator('#reference-year').select_option('1820');assert '1820' in page.locator('#reference-map-status').inner_text();assert '無縣界' in page.locator('#reference-map-status').inner_text()
 page.locator('#context-world').click();before=m.get_attribute('viewBox');m.focus();page.keyboard.press('ArrowRight');assert m.get_attribute('viewBox')!=before
 page.locator('#context-map-home').click();page.locator('#reference-year').select_option('1911');page.locator('#context-zoom-in').click();page.wait_for_timeout(200)
 # Source links and hover menus retain their two destinations.
 page.locator('#reader a[data-person-link]').first.hover();page.wait_for_selector('#entity-card:not([hidden])');assert page.locator('#entity-card a').count()>=2;page.keyboard.press('Escape')
 page.screenshot(path='/mnt/data/ren-wen-zeng-full-map.png')
 page.evaluate("w=>window.dispatchEvent(new CustomEvent('renwen:navigate',{detail:{witness:w}}))",'qsg');page.wait_for_selector('#qsg-02');page.wait_for_selector('[data-unit-occurrence="occ-qsg-yili-memorial"]');assert page.locator('#reader p[id]').count()==4;assert '伊犁一役' in page.locator('#qsg-02').inner_text()
 q=b.new_page(viewport={'width':1200,'height':900});q.on('pageerror',lambda e:errors.append(str(e)));load(q,'texts.html');q.wait_for_selector('#text-unit h1');q.select_option('#unit-select','text-zeng-jize-yili-memorial');q.wait_for_timeout(250);assert '伊犁一役' in q.locator('.unit-reading').inner_text();assert q.locator('.unit-breadcrumb a').count()==1
 q.screenshot(path='/mnt/data/ren-wen-quotation-layer.png',full_page=True)
 q.locator('[data-set-locale="en"]').click();assert 'Read in full context' in q.locator('#text-unit').inner_text();assert '伊犁一役' in q.locator('.unit-reading').inner_text()
 mobile=b.new_page(viewport={'width':390,'height':844},has_touch=True,is_mobile=True,reduced_motion='reduce');mobile.on('pageerror',lambda e:errors.append(str(e)));load(mobile,'index.html');mobile.wait_for_selector('#historic-map');assert mobile.evaluate('document.documentElement.scrollWidth')<=391
 assert not errors,errors
 b.close();print('Text completeness, source hover, nested quotation, map drag/zoom/levels and mobile DOM checks passed.')
