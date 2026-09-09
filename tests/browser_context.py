"""Browser integration against local files in memory, not a live-site deployment test.
Requires Playwright and Chromium; run: python tests/browser_context.py.
"""
from pathlib import Path
import re,json,base64,os,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def datauri(mime,raw):return 'data:'+mime+';base64,'+base64.b64encode(raw).decode()
land=datauri('image/svg+xml',(ROOT/'assets/land.svg').read_bytes())
modules={}
def module(path):
 path=path.resolve()
 if path in modules:return modules[path]
 text=path.read_text().replace('assets/land.svg',land)
 text=re.sub(r"from\s+(['\"])(\./[^'\"]+)\1",lambda m:'from '+json.dumps(module(path.parent/m[2])),text)
 modules[path]=datauri('text/javascript',text.encode())
 return modules[path]
html=(ROOT/'index.html').read_text()
entries=re.findall(r'<script type="module" src="([^"]+)"></script>',html)
html=re.sub(r'<script type="module"[^>]*></script>','',html)
html=re.sub(r'<link rel="stylesheet" href="([^"]+)">',lambda m:'<style>'+(ROOT/m[1]).read_text()+'</style>',html).replace('assets/land.svg',land)
files={str(p.relative_to(ROOT)):p.read_text() for p in (ROOT/'data').rglob('*') if p.is_file() and p.suffix in ['.json','.html']}
with sync_playwright() as p:
 executable=os.environ.get('BROWSER_EXECUTABLE') or shutil.which('chromium')
 b=p.chromium.launch(**({'executable_path':executable} if executable else {}),headless=True,args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1480,'height':1020},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html)
 page.evaluate('''files=>{
  const store=new Map([['ren-wen:language:v1','en']]);Object.defineProperty(window,'localStorage',{value:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)}});
  window.fetch=async path=>new Response(files[String(path)],{status:Object.hasOwn(files,String(path))?200:404});
 }''',files)
 for entry in entries:page.add_script_tag(type='module',content='import '+json.dumps(module(ROOT/entry)))
 page.wait_for_selector('#context-timeline [data-person-row]',timeout=8000)
 page.wait_for_timeout(500)
 print('rows',page.locator('#context-timeline [data-person-row]').count(),'paths',page.locator('#life-trajectories [data-route]').count(),'errors',errors)

 page.locator('#eccp-03').evaluate('(p)=>p.click()')
 page.wait_for_timeout(500)
 print('active',page.locator('#reader p.active').get_attribute('id'))
 print(page.locator('#context-timeline [data-person-row]').evaluate_all('(nodes)=>nodes.map(n=>[n.dataset.personRow,n.getAttribute("transform"),n.getAttribute("class")])'))

 assert not errors,errors
 assert page.locator('#context-timeline [data-family]').count()==1
 def visual_order():
  return page.locator('#context-timeline [data-person-row]').evaluate_all('(nodes)=>nodes.sort((a,b)=>a.transform.baseVal.getItem(0).matrix.f-b.transform.baseVal.getItem(0).matrix.f).map(n=>n.dataset.personRow)')
 assert visual_order()[:3]==['person-zeng-jize','person-macartney','person-guo-songtao']
 page.locator('#group-people').uncheck();page.wait_for_timeout(380)
 assert visual_order()[:2]==['person-zeng-jize','person-zeng-guofan']
 page.locator('#group-people').check();page.wait_for_timeout(380)
 assert visual_order()[:3]==['person-zeng-jize','person-macartney','person-guo-songtao']
 page.locator('#eccp-08').evaluate('(p)=>p.click()');page.wait_for_timeout(400)
 assert visual_order()[:2]==['person-zeng-jize','person-chonghou']
 assert page.locator('#context-timeline .name').first.get_attribute('class')=='name'
 assert page.locator('#reader a[data-person-link]').first.get_attribute('href').startswith('profiles.html#')
 # Scrolling changes the active paragraph and groups the corresponding people.
 page.locator('#reader').evaluate('''el=>{el.style.scrollBehavior='auto';const p=document.getElementById('eccp-03');el.scrollTop+=p.getBoundingClientRect().top-el.getBoundingClientRect().top-100;}''')
 page.wait_for_timeout(450)
 assert page.locator('#reader p.active').get_attribute('id')=='eccp-03'
 assert visual_order()[:3]==['person-zeng-jize','person-macartney','person-guo-songtao']
 page.locator('#eccp-08').evaluate('(p)=>p.click()');page.wait_for_timeout(400)
 # Wheel, buttons, keyboard, and pan preserve an independently controlled camera.
 old=page.locator('#historic-map').get_attribute('viewBox')
 page.locator('#context-zoom-in').click();new=page.locator('#historic-map').get_attribute('viewBox');assert old!=new
 page.locator('#historic-map').focus();page.keyboard.press('ArrowRight')
 assert page.locator('#historic-map').get_attribute('viewBox')!=new
 page.keyboard.press('Home');assert page.locator('#historic-map').get_attribute('viewBox')=='0 0 170 80'
 page.locator('#context-zoom-in').click()
 box=page.locator('#historic-map').bounding_box();x,y=box['x']+box['width']*.55,box['y']+box['height']*.55
 before=page.locator('#historic-map').get_attribute('viewBox')
 page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+40,y+15,steps=10);page.mouse.up()
 assert page.locator('#historic-map').get_attribute('viewBox')!=before
 page.locator('#context-map-home').click()
 # A simple marker click must not be swallowed by pointer capture.
 page.locator('#context-places [data-place-id="place-shanghai"] circle').click()
 assert page.locator('#jurisdiction-county').input_value()=='shanghai'
 page.locator('#jurisdiction-province').select_option('hunan')
 page.locator('#jurisdiction-prefecture').select_option('changsha')
 page.locator('#jurisdiction-county').select_option('xiangxiang')
 assert '湖南省 › 長沙府 › 湘鄉縣' in page.locator('#jurisdiction-evidence').inner_text()
 # Time and person filters must not display another person's or source's travel.
 page.locator('#trajectory-scope').select_option('passage');assert page.locator('#life-trajectories [data-route]').count()==1
 page.locator('#trajectory-person').select_option('person-zeng-guofan');assert page.locator('#life-trajectories [data-route]').count()==0
 page.locator('#trajectory-person').select_option('person-zeng-jize')
 page.locator('#trajectory-scope').select_option('all');assert page.locator('#life-trajectories [data-route]').count()==4
 page.locator('#context-journeys [data-journey="russia-1880"]').click()
 assert page.locator('#context-evidence').is_visible()
 assert '1880-07-30' in page.locator('#context-evidence').inner_text()
 page.locator('#context-evidence .close').click()
 # Family evidence navigation can switch the source without fabricating an alignment.
 page.locator('[data-family-evidence]').click()
 page.locator('#context-evidence [data-witness="qsg"]').click()
 page.wait_for_function("document.querySelector('#reader p.active')?.id === 'qsg-01'")
 page.wait_for_timeout(400)
 assert page.locator('#life-trajectories [data-route]').count()==0
 assert 'No documented journey' in page.locator('#context-journeys').inner_text()
 page.locator('#source-select').select_option('eccp')
 page.wait_for_function("document.querySelector('#reader p.active')?.id === 'eccp-01'")
 page.wait_for_timeout(400)
 # Optional local boundary loading with clearly synthetic test-only geometry.
 fixture={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'jurisdictionId':'xiangxiang','level':'county','startYear':1870,'endYear':1885,'source':'https://example.org/synthetic-fixture','license':'CC0-1.0','attribution':'Synthetic test fixture'},'geometry':{'type':'Polygon','coordinates':[[[110,27],[111,27],[111,28],[110,27]]]}}]}
 page.locator('#year').evaluate('(el)=>{el.value=1880;el.dispatchEvent(new Event("input",{bubbles:true}));}');page.wait_for_timeout(200)
 page.locator('#boundary-file').set_input_files({'name':'fixture.geojson','mimeType':'application/json','buffer':json.dumps(fixture).encode()})
 page.wait_for_timeout(200);assert page.locator('#historical-boundaries path').count()==1
 page.locator('#year').evaluate('(el)=>{el.value=1886;el.dispatchEvent(new Event("input",{bubbles:true}));}');page.wait_for_timeout(200)
 assert page.locator('#historical-boundaries path').count()==0
 page.locator('.context-jurisdictions summary').click();page.locator('#clear-boundaries').click()
 page.locator('#follow').check()
 page.locator('#eccp-04').evaluate('(p)=>p.click()');page.wait_for_timeout(400)
 page.locator('#context-map-home').click()
 screenshot=Path(os.environ.get('RENWEN_SCREENSHOT',str(ROOT/'build/context-desktop.png')))
 screenshot.parent.mkdir(parents=True,exist_ok=True)
 page.screenshot(path=str(screenshot),full_page=True)
 page.set_viewport_size({'width':900,'height':1000});page.wait_for_timeout(150)
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(150)
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 assert page.locator('#historic-map').is_visible()
 assert not errors,errors
 print('Browser fixture checks passed: reordering, family evidence, map pan/zoom and marker clicks, person/source/time filters, local geometry, responsive layouts.')

 b.close()
