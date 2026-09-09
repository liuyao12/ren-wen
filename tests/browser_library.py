"""Browser integration with local file fixtures; does not claim a live network test."""
from pathlib import Path
import base64,json,re,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
modules={}
def uri(mime,raw):return 'data:'+mime+';base64,'+base64.b64encode(raw).decode()
land=uri('image/svg+xml',(ROOT/'assets/land.svg').read_bytes())
def module(path):
    path=path.resolve()
    if path in modules:return modules[path]
    text=path.read_text().replace('assets/land.svg',land)
    text=re.sub(r"from\s+(['\"])(\./[^'\"]+)\1",lambda m:'from '+json.dumps(module(path.parent/m[2])),text)
    modules[path]=uri('text/javascript',text.encode());return modules[path]
files={str(p.relative_to(ROOT)):p.read_text() for p in (ROOT/'data').rglob('*') if p.is_file() and p.suffix in ['.json','.html']}
def load(page,filename):
    html=(ROOT/filename).read_text();entries=re.findall(r'<script type="module" src="([^"]+)"',html)
    html=re.sub(r'<script type="module"[^>]*></script>','',html)
    html=re.sub(r'<link rel="stylesheet" href="([^"]+)">',lambda m:'<style>'+(ROOT/m[1]).read_text()+'</style>',html).replace('assets/land.svg',land)
    page.set_content(html)
    page.evaluate('''files=>{const store=new Map([['ren-wen:language:v1','en']]);Object.defineProperty(window,'localStorage',{value:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)}});window.fetch=async path=>new Response(files[String(path)],{status:Object.hasOwn(files,String(path))?200:404});}''',files)
    for e in entries:page.add_script_tag(type='module',content='import '+json.dumps(module(ROOT/e)))
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True,executable_path=shutil.which('chromium'))
    page=b.new_page(viewport={'width':1600,'height':1000},reduced_motion='reduce')
    errors=[];page.set_default_timeout(7000);page.on('pageerror',lambda e:(errors.append(str(e)),print('JSERROR',str(e),flush=True)))
    load(page,'index.html');print('Loaded',flush=True);page.wait_for_selector('#context-timeline [data-person-row]');page.wait_for_selector('#reader a[data-work-link]');page.wait_for_timeout(350)
    print('Startup ready',flush=True);assert page.locator('#reader p[id]').count()==21
    assert page.locator('a a').count()==0
    print('Hovering Guo',flush=True);page.locator('#eccp-03-m02').scroll_into_view_if_needed();page.wait_for_timeout(250);page.locator('#eccp-03-m02').hover();page.wait_for_selector('#entity-card:not([hidden])')
    assert page.locator('#entity-card a',has_text='Read ECCP entry').get_attribute('href')=='./#eccp-guo-songtao'
    assert '郭嵩燾' in page.locator('#entity-card h2').inner_text()
    # The pointer can cross from the source name into the interactive card.
    page.locator('#entity-card a').first.hover();page.wait_for_timeout(300);assert page.locator('#entity-card').is_visible()
    page.screenshot(path='/mnt/data/ren-wen-eccp-hover.png')
    page.keyboard.press('Escape');assert page.locator('#entity-card').is_hidden()
    a=page.locator('#eccp-01-m04').locator('..');a.focus();page.keyboard.press('ArrowDown');page.keyboard.press('Escape');assert page.locator('#entity-card').is_hidden()
    print('Switching',flush=True);page.locator('#source-select').select_option('eccp-guo-songtao');page.wait_for_selector('#eccp-guo-songtao-01');page.wait_for_timeout(250)
    assert '郭嵩燾' in page.locator('#reader h1').inner_text()
    page.locator('#reader a[data-work-link]').first.hover();page.wait_for_selector('#entity-card:not([hidden])')
    workhref=page.locator('#entity-card a',has_text='Work profile').get_attribute('href');assert workhref.startswith('works.html#work-')
    assert page.locator('#entity-card a',has_text='Read this ECCP passage').get_attribute('href').startswith('./?passage=')
    page.locator('#entity-card .card-review').click();page.wait_for_selector('#inspector:not([hidden])');assert 'work' in page.locator('#inspector-body').inner_text()
    page.locator('#close-inspector').click();page.locator('#source-select').select_option('eccp');page.wait_for_selector('#eccp-01');page.wait_for_timeout(250)
    page.locator('#eccp-03-m01').hover();page.wait_for_selector('#entity-card:not([hidden])')
    assert page.locator('#entity-card a',has_text='Discussed in ECCP').count()==1
    assert page.locator('#entity-card a',has_text='Read ECCP entry').count()==0
    page.keyboard.press('Escape');page.locator('#review-names').check();page.locator('#eccp-01-m04').click();page.wait_for_selector('#inspector:not([hidden])');assert 'eccp-01-m04' in page.locator('#inspector-body').inner_text()
    # Every annotated name and work has a native local destination on every new source.
    page.locator('#close-inspector').click();page.locator('#review-names').uncheck()
    for wid in ['eccp','eccp-guo-songtao','eccp-dong-xun','eccp-chonghou']:
        page.locator('#source-select').select_option(wid);page.wait_for_selector('#'+wid+'-01');page.wait_for_timeout(220)
        assert page.locator('#reader p[id] a a').count()==0
        assert page.locator('#reader [data-entity^="work-"]').count()==page.locator('#reader a[data-work-link]').count()
        assert page.locator('#reader [data-entity^="person-"]').count()<=page.locator('#reader a[data-person-link]').count()
    assert not errors,errors
    w=b.new_page(viewport={'width':1300,'height':1000});w.on('pageerror',lambda e:errors.append(str(e)));load(w,'works.html');w.wait_for_selector('#work h1')
    w.evaluate('(id)=>location.hash=id',workhref.split('#')[1]);w.wait_for_timeout(150)
    assert w.locator('.mentions-list a').first.get_attribute('href').startswith('./?passage=')
    w.screenshot(path='/mnt/data/ren-wen-work-profile.png',full_page=True)
    p=b.new_page();p.on('pageerror',lambda e:errors.append(str(e)));load(p,'profiles.html');p.wait_for_selector('#profile h1');p.select_option('#profile-select','person-guo-songtao');p.wait_for_timeout(150)
    assert 'Works and contributions' in p.locator('#profile').inner_text()
    assert p.locator('a',has_text='Read ECCP entry').count()==1
    touch=b.new_page(viewport={'width':390,'height':844},has_touch=True,is_mobile=True,reduced_motion='reduce');touch.on('pageerror',lambda e:errors.append(str(e)));load(touch,'index.html');touch.wait_for_selector('#entity-card',state='attached');touch.wait_for_selector('#reader a[data-person-link]');touch.locator('#eccp-01-m04').tap();touch.wait_for_selector('#entity-card:not([hidden])')
    rect=touch.locator('#entity-card').bounding_box();assert rect['x']>=0 and rect['x']+rect['width']<=391
    assert not errors,errors
    print('Library browser fixtures passed: hover, keyboard, touch, source switching, work profiles, review and backlinks.')
    b.close()
