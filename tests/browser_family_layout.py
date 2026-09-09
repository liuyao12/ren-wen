"""Family layout and stacked-map checks. Default: local fixtures; --url: real served app."""
from pathlib import Path
import argparse, base64, json, os, re, shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url')
parser.add_argument('--output',type=Path,default=ROOT/'build/family-browser')
args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)

def fixture(page):
    modules={}
    def uri(mime,raw):return 'data:'+mime+';base64,'+base64.b64encode(raw).decode()
    land=uri('image/svg+xml',(ROOT/'assets/land.svg').read_bytes())
    images={str(p.relative_to(ROOT)):uri('image/png',p.read_bytes()) for p in (ROOT/'assets/maps').glob('*.png')}
    def module(path):
        path=path.resolve()
        if path not in modules:
            text=path.read_text().replace('assets/land.svg',land).replace('href:layer.file,','href:window.__mapImages[layer.file],')
            text=re.sub(r"from\s+(['\"])(\./[^'\"]+)\1",lambda m:'from '+json.dumps(module(path.parent/m[2])),text)
            modules[path]=uri('text/javascript',text.encode())
        return modules[path]
    html=(ROOT/'index.html').read_text();entries=re.findall(r'<script type="module" src="([^"]+)"',html)
    html=re.sub(r'<script\b[^>]*></script>','',html)
    html=re.sub(r'<link rel="stylesheet" href="([^"]+)">',lambda m:'<style>'+(ROOT/m[1]).read_text()+'</style>',html)
    page.set_content(html.replace('assets/land.svg',land))
    files={str(p.relative_to(ROOT)):p.read_text() for p in (ROOT/'data').rglob('*') if p.is_file() and p.suffix in ['.json','.html']}
    page.evaluate('''({files,images})=>{const store=new Map();Object.defineProperty(window,'localStorage',{value:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)}});window.__mapImages=images;window.fetch=async path=>new Response(files[String(path)],{status:Object.hasOwn(files,String(path))?200:404});}''',{'files':files,'images':images})
    for e in entries:page.add_script_tag(type='module',content='import '+json.dumps(module(ROOT/e)))

def settle(page):page.wait_for_timeout(330)
def choose(page,witness):
    page.locator('#source-select').select_option(witness);page.wait_for_selector('#'+witness+'-01');settle(page)
def scroll_to(page,id):
    page.locator('#reader').evaluate('''(reader,id)=>{reader.style.scrollBehavior='auto';const p=document.getElementById(id);reader.scrollTop+=p.getBoundingClientRect().top-reader.getBoundingClientRect().top-75;}''',id)
    settle(page)
def visual_rows(page):
    return page.locator('#context-timeline [data-row-key]').evaluate_all('(ns)=>ns.map(n=>({id:n.dataset.personRow,key:n.dataset.rowKey,role:n.dataset.familyRole,y:n.transform.baseVal.getItem(0).matrix.f})).sort((a,b)=>a.y-b.y)')
report={'mockedNetwork':not bool(args.url),'errors':[]}
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=os.environ.get('BROWSER_EXECUTABLE') or shutil.which('chromium') or shutil.which('google-chrome'),headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1500,'height':1000},reduced_motion='reduce');page.set_default_timeout(15000)
    page.on('pageerror',lambda e:report['errors'].append(str(e)))
    try:
        if args.url:page.goto(args.url,wait_until='networkidle',timeout=60000)
        else:fixture(page)
        page.wait_for_selector('#context-timeline [data-row-key]');choose(page,'eccp-zeng-guofan')
        reader_before=page.locator('#reader p[id]').all_text_contents()
        assert len(reader_before)==17
        text=page.locator('.text-panel').bounding_box();time=page.locator('.time-panel').bounding_box();mp=page.locator('.map-panel').bounding_box()
        assert abs(text['width']-time['width'])<=2
        assert abs(time['x']-mp['x'])<=2 and abs(time['width']-mp['width'])<=2
        assert mp['y']>=time['y']+time['height']-2
        assert text['height']>=time['height']+mp['height']-2
        report['layout']={'text':text,'timeline':time,'map':mp}
        initial=visual_rows(page)
        assert [r['id'] for r in initial[:3]]==['person-zeng-yuping','person-zeng-linshu','person-zeng-guofan']
        assert page.locator('[data-family-summary="children"]').count()==1
        assert page.locator('[data-family-role="spouses"]').count()==0
        assert page.locator('#context-timeline [data-family]').count()>=9
        axis=page.locator('#context-timeline').get_attribute('data-axis')
        page.locator('#expand-family').click();settle(page)
        rows=visual_rows(page);assert [r['role'] for r in rows[:3]]==['grandparents','parents','self']
        assert sum(r['role']=='children' for r in rows)==7
        page.locator('#expand-family').click();settle(page)
        # A paragraph with active children pushes non-family figures down; subsequent prose compacts them.
        scroll_to(page,'eccp-zeng-guofan-15')
        assert page.locator('#reader p.active').get_attribute('id')=='eccp-zeng-guofan-15'
        assert page.locator('[data-person-row="person-zeng-jize"]').count()==1
        assert sum(r['role']=='children' for r in visual_rows(page))==7
        scroll_to(page,'eccp-zeng-guofan-05')
        assert page.locator('#reader p.active').get_attribute('id')=='eccp-zeng-guofan-05'
        rows=visual_rows(page);self_y=next(r['y'] for r in rows if r['role']=='self');other_y=next(r['y'] for r in rows if r['role']=='other')
        assert 0<other_y-self_y<85
        assert page.locator('[data-family-summary="children"]').count()==1
        assert page.locator('#context-timeline').get_attribute('data-axis')==axis
        report['focusGap']=other_y-self_y;report['generationOrder']=True
        page.screenshot(path=str(args.output/'family-focus.png'))
        page.locator('[data-set-locale="en"]').click();settle(page)
        assert page.locator('#reader p[id]').all_text_contents()==reader_before
        assert page.locator('#reader p.active').get_attribute('id')=='eccp-zeng-guofan-05'
        assert 'Follow paragraph focus' in page.locator('.context-options').inner_text()
        page.locator('[data-set-locale="zh-Hant"]').click();settle(page)
        page.locator('.family-evidence summary').click()
        page.locator('[data-family-evidence="r-zeng-guofan-child-of-zeng-linshu"]').click()
        assert page.locator('#context-evidence').is_visible()
        assert page.locator('#context-evidence [data-evidence-passage="eccp-zeng-guofan-01"]').count()==1
        page.locator('#context-evidence .close').click();page.locator('.family-evidence summary').click()
        # The map still accepts real pointer and keyboard input in its new position.
        m=page.locator('#historic-map');m.scroll_into_view_if_needed();b=m.bounding_box();x=b['x']+b['width']*.5;y=b['y']+b['height']*.4
        before=m.get_attribute('viewBox');page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+32,y+14,steps=5);page.mouse.up();assert m.get_attribute('viewBox')!=before
        before=m.get_attribute('viewBox');page.mouse.wheel(0,-180);settle(page);assert m.get_attribute('viewBox')!=before
        for _ in range(4):page.locator('#context-zoom-in').click()
        assert page.locator('[data-reference-year="1911"][data-reference-level="county"]').get_attribute('visibility')=='visible'
        report['mapDragZoomCounty']=True
        page.locator('#context-map-home').click();scroll_to(page,'eccp-zeng-guofan-01')
        page.locator('.time-body').evaluate('(n)=>n.scrollTop=0');page.locator('.context-map-body').evaluate('(n)=>n.scrollTop=0');settle(page)
        page.screenshot(path=str(args.output/'family-desktop.png'))
        choose(page,'eccp')
        page.locator('#expand-family').click();settle(page)
        rows=visual_rows(page);assert [r['id'] for r in rows[:3]]==['person-zeng-linshu','person-zeng-guofan','person-zeng-jize']
        page.locator('#expand-family').click();settle(page)
        for w in (900,760,390):
            page.set_viewport_size({'width':w,'height':950});settle(page)
            assert page.evaluate('document.documentElement.scrollWidth')<=w+1
            if w==900:
                assert page.locator('.map-panel').bounding_box()['x']>=449
            else:
                assert page.locator('.map-panel').bounding_box()['y']>page.locator('.time-panel').bounding_box()['y']
        report['responsive']=True
        assert not report['errors'],report['errors'];report['passed']=True
    except Exception as e:
        report['passed']=False;report['error']=str(e);page.screenshot(path=str(args.output/'failure.png'),full_page=True);raise
    finally:
        (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));browser.close()
