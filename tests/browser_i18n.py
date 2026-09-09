"""Bilingual browser integration using local fixtures, not a live-site network test."""
from pathlib import Path
import base64
import json
import re
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
MODULES = {}
FILES = {str(p.relative_to(ROOT)): p.read_text() for p in (ROOT / 'data').rglob('*') if p.is_file() and p.suffix in ['.json', '.html']}
KEY = 'ren-wen:language:v1'

def uri(mime, data):
    return 'data:' + mime + ';base64,' + base64.b64encode(data).decode()

LAND = uri('image/svg+xml', (ROOT / 'assets/land.svg').read_bytes())

def module(path):
    path = path.resolve()
    if path not in MODULES:
        text = path.read_text().replace('assets/land.svg', LAND)
        text = re.sub(r"from\s+(['\"])(\./[^'\"]+)\1", lambda m: 'from ' + json.dumps(module(path.parent / m[2])), text)
        MODULES[path] = uri('text/javascript', text.encode())
    return MODULES[path]

def load(page, filename, saved=None, blocked=False):
    html = (ROOT / filename).read_text()
    entries = re.findall(r'<script type="module" src="([^"]+)"', html)
    html = re.sub(r'<script\b[^>]*></script>', '', html)
    html = re.sub(r'<link rel="stylesheet" href="([^"]+)">', lambda m: '<style>' + (ROOT / m[1]).read_text() + '</style>', html)
    page.set_content(html.replace('assets/land.svg', LAND))
    page.evaluate('''({files,saved,blocked})=>{
      const store=new Map(Object.entries(saved||{}));
      Object.defineProperty(window,'localStorage',{configurable:true,value:{
        getItem:key=>{if(blocked)throw new Error('Storage disabled');return store.get(key)||null;},
        setItem:(key,value)=>{if(blocked)throw new Error('Storage disabled');store.set(key,value);}
      }});
      window.savedPreferences=()=>Object.fromEntries(store);
      window.fetch=async path=>new Response(files[String(path)],{status:Object.hasOwn(files,String(path))?200:404});
    }''', {'files': FILES, 'saved': saved or {}, 'blocked': blocked})
    page.add_script_tag(content=(ROOT / 'assets/locale-init.js').read_text())
    for entry in entries:
        page.add_script_tag(type='module', content='import ' + json.dumps(module(ROOT / entry)))

def language(page, code):
    page.locator(f'[data-set-locale="{code}"]').click()
    page.wait_for_function('(value)=>document.documentElement.lang===value', arg=code)
    page.wait_for_timeout(100)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path=shutil.which('chromium'))
    errors = []
    def newpage(**kwargs):
        page = browser.new_page(reduced_motion='reduce', **kwargs)
        page.set_default_timeout(10000)
        page.on('pageerror', lambda err: errors.append(str(err)))
        return page
    page = newpage(viewport={'width': 1600, 'height': 1000})
    load(page, 'index.html')
    page.wait_for_selector('#context-timeline [data-person-row]')
    page.wait_for_selector('#reader a[data-work-link]')
    page.wait_for_timeout(250)
    assert page.locator('html').get_attribute('lang') == 'zh-Hant'
    assert page.locator('a[href="profiles.html"]').first.inner_text() == '人物'
    assert page.locator('#source-info').inner_text() == '文獻與版本'
    assert page.locator('#eccp-01').get_attribute('lang') == 'en'
    source = page.locator('#reader > p[id]').evaluate_all('(nodes)=>nodes.map(n=>[n.id,n.textContent,n.lang])')
    names = page.locator('#reader .person-heading h1').inner_text()
    page.locator('#eccp-03-m02').scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    page.locator('#eccp-03-m02').hover()
    page.wait_for_selector('#entity-card:not([hidden])')
    assert page.locator('#entity-card nav a').first.inner_text() == '人物資料'
    assert page.locator('#entity-card a', has_text='閱讀 ECCP 本傳').get_attribute('href') == './#eccp-guo-songtao'
    page.screenshot(path='/mnt/data/ren-wen-chinese-hover.png')
    page.keyboard.press('Escape')
    # Switch with real view state and a partially written review proposal.
    page.locator('#context-zoom-in').click()
    page.locator('#review-names').check()
    page.locator('#eccp-01-m04').click()
    page.wait_for_selector('#inspector:not([hidden])')
    draft = '保留的中文理由 / draft with dates 1839 and name 曾國藩'
    page.locator('#reason').fill(draft)
    page.locator('#year').evaluate('(n)=>{n.value=1881;n.dispatchEvent(new Event("input",{bubbles:true}));}')
    saved = page.evaluate('''()=>({passage:document.querySelector('#reader p.active').id,source:document.querySelector('#source-select').value,
      year:document.querySelector('#year').value,view:document.querySelector('#historic-map').getAttribute('viewBox'),
      scroll:document.querySelector('#reader').scrollTop,candidate:document.querySelector('#candidate').value,hash:location.hash})''')
    # The inspector overlays the toolbar, so a pointer-free activation tests the same handler.
    page.locator('[data-set-locale="en"]').dispatch_event('click')
    page.wait_for_timeout(200)
    assert page.locator('html').get_attribute('lang') == 'en'
    assert page.locator('#reason').input_value() == draft
    assert page.locator('#source-info').inner_text() == 'Source & edition'
    assert page.locator('#propose').inner_text() == 'Add to review queue'
    assert page.locator('#candidate').input_value() == saved['candidate']
    assert page.locator('#reader > p[id]').evaluate_all('(nodes)=>nodes.map(n=>[n.id,n.textContent,n.lang])') == source
    assert page.locator('#reader .person-heading h1').inner_text() == names
    assert page.locator('#historic-map').get_attribute('viewBox') == saved['view']
    assert page.locator('#year').input_value() == saved['year']
    assert page.locator('#source-select').input_value() == saved['source']
    assert page.locator('#reader p.active').get_attribute('id') == saved['passage']
    assert page.evaluate('location.hash') == saved['hash']
    # Header height is fixed on this desktop; reading position must not jump.
    assert abs(page.locator('#reader').evaluate('(n)=>n.scrollTop') - saved['scroll']) <= 2
    prefs = page.evaluate('savedPreferences()')
    assert prefs[KEY] == 'en'
    page.locator('#close-inspector').click()
    page.locator('#review-names').uncheck()
    # New pages use the same persisted preference while keeping canonical Chinese data.
    person = newpage(viewport={'width': 1300, 'height': 1000})
    load(person, 'profiles.html', prefs)
    person.wait_for_selector('#profile h1')
    assert person.locator('html').get_attribute('lang') == 'en'
    assert 'Identity · 名籍' in person.locator('#profile').inner_text()
    assert '道光十九年己亥' in person.locator('#profile').inner_text()
    person.locator('#profile details').first.evaluate('(n)=>n.open=true')
    language(person, 'zh-Hant')
    assert '名籍' in person.locator('#profile').inner_text()
    assert person.locator('#profile details').first.evaluate('(n)=>n.open')
    assert person.locator('#profile h1').inner_text() == '[湖南湘鄉] 曾紀澤（劼剛）'
    work = newpage(viewport={'width': 1300, 'height': 1000})
    load(work, 'works.html', person.evaluate('savedPreferences()'))
    work.wait_for_selector('#work h1')
    work.evaluate("location.hash='work-zhuangzi-jishi'")
    work.wait_for_function("document.querySelector('#work h1')?.textContent==='莊子集釋'")
    work.locator('#work-search').fill('莊')
    quote = work.locator('#work q').first.text_content()
    language(work, 'en')
    assert work.locator('#work-search').input_value() == '莊'
    assert work.locator('#work h1').inner_text() == '莊子集釋'
    assert work.locator('#work q').first.text_content() == quote
    assert 'Titles as attested' in work.locator('#work').inner_text()
    assert 'works' in work.locator('#work-count').inner_text()
    # Chinese source text and its punctuation visibility are unaffected by UI switching.
    page.locator('#source-select').select_option('qsg')
    page.wait_for_selector('#qsg-01')
    page.locator('#punctuation').check()
    qsg = page.locator('#qsg-01').text_content()
    language(page, 'zh-Hant')
    assert page.locator('#punctuation').is_checked()
    assert page.locator('#qsg-01').text_content() == qsg
    assert page.locator('#qsg-01').get_attribute('lang') == 'zh-Hant'
    # Even a fake translation marker inside a source span is explicitly protected.
    page.evaluate('''()=>{const x=document.createElement('span');x.dataset.i18n='People';x.id='protected-fixture';x.textContent='People';document.querySelector('#qsg-01').append(x);}''')
    page.wait_for_timeout(100)
    assert page.locator('#protected-fixture').text_content() == 'People'
    # Narrow layout and storage-denied sessions still have a usable switch.
    mobile = newpage(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True)
    load(mobile, 'index.html', blocked=True)
    mobile.wait_for_selector('#reader a[data-person-link]')
    assert mobile.locator('html').get_attribute('lang') == 'zh-Hant'
    language(mobile, 'en')
    assert mobile.locator('[data-set-locale="en"]').get_attribute('aria-pressed') == 'true'
    language(mobile, 'zh-Hant')
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    assert not errors, errors
    print('Bilingual browser fixtures passed: source invariance, hover choices, language persistence, draft preservation, profile/work identity, map/time/scroll state, punctuation, protected text and mobile/storage restrictions.')
    browser.close()
