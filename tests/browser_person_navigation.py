"""DOM integration with in-memory source fixtures; never navigates to external sites."""
from pathlib import Path
import re
import json
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def code(path):
    text = (ROOT / path).read_text(encoding='utf-8')
    text = re.sub(r'^import .*?;\s*$', '', text, flags=re.M)
    return text.replace('export ', '')

# This is a synthetic reading fixture, not a replacement or edit to corpus text.
HTML = '''<!doctype html><html><head><meta charset="utf-8"></head><body>
<select id="source-select"><option value="eccp">ECCP</option></select><input type="checkbox" id="review-names"><div id="status"></div>
<div id="reader"><div class="kicker">ECCP</div><h1>Original title</h1>
<p id="eccp-01">He met <a href="https://en.wikisource.org/wiki/Eminent_Chinese_of_the_Ch%27ing_Period/Ts%C3%AAng_Kuo-fan"><span id="m1" data-entity="person-zeng-guofan" role="button" tabindex="0">Tsêng Kuo-fan</span></a> [q. v.].</p>
<p id="eccp-03"><span id="m2" data-entity="person-macartney">Samuel Halliday Macartney</span> (see under <a href="https://en.wikisource.org/wiki/Eminent_Chinese_of_the_Ch%27ing_Period/Kuo_Sung-tao"><span id="m3" data-entity="person-guo-songtao">Kuo Sung-tao</span></a>).</p>
<p id="eccp-17">See <a href="https://en.wikisource.org/wiki/Eminent_Chinese_of_the_Ch%27ing_Period/Tung_Hs%C3%BCn" target="_blank">Tung Hsün</a>.</p></div>
<script>document.getElementById('reader').addEventListener('click',e=>{const m=e.target.closest('[data-entity]');if(m){e.preventDefault();document.body.dataset.inspected=m.id;}});</script></body></html>'''

files = {str(p.relative_to(ROOT)): json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'data').rglob('*.json')}
mock = 'globalThis.fetch = async path => ({ok:Object.hasOwn(fixtures,path),status:Object.hasOwn(fixtures,path)?200:404,json:async()=>structuredClone(fixtures[path])});'
deps = code('assets/core.js') + '\nconst h=escapeHTML;\n' + code('assets/profiles.js') + '\n' + code('assets/person-display.js')

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path=shutil.which('chromium') or shutil.which('google-chrome'))
    page = browser.new_page()
    page.set_content(HTML)
    page.evaluate('(fixtures)=>{' + mock + '\n' + deps + '\n' + code('assets/person-links.js') + '}', files)
    page.wait_for_selector('a[data-person-link="person-dong-xun"]')
    assert page.locator('a a').count() == 0
    assert page.locator('#reader h1').inner_text() == '[湖南湘鄉] 曾紀澤（劼剛）'
    assert '道光十九年己亥' in page.locator('.person-heading').inner_text()
    assert page.locator('#eccp-01').inner_text() == 'He met Tsêng Kuo-fan [q. v.].'
    assert page.locator('#m1').get_attribute('role') is None
    assert page.locator('#m1').get_attribute('tabindex') is None
    for pid in ['person-zeng-guofan','person-macartney','person-guo-songtao','person-dong-xun']:
        assert page.locator(f'a[data-person-link="{pid}"]').get_attribute('href') == 'profiles.html#' + pid
    page.locator('#review-names').check()
    page.locator('#m1').click()
    assert page.locator('body').get_attribute('data-inspected') == 'm1'
    page.locator('#review-names').uncheck()
    page.evaluate("document.querySelector('#reader').addEventListener('click',e=>{document.body.dataset.nativeDefault=String(!e.defaultPrevented);e.preventDefault();},true)")
    page.locator('#m1').click()
    assert page.locator('body').get_attribute('data-native-default') == 'true'
    page.evaluate("document.querySelector('#reader').innerHTML='<h1>Next source</h1><p id=\"qsg-01\"><span data-entity=\"person-chonghou\" id=\"c1\">崇厚</span></p>'")
    page.wait_for_selector('a[data-person-link="person-chonghou"]')
    assert page.locator('.person-heading').count() == 1

    page = browser.new_page()
    html = re.sub(r'<script\b.*?</script>', '', (ROOT/'profiles.html').read_text(encoding='utf-8'), flags=re.S)
    html = re.sub(r'<link\b[^>]*>', '', html)
    page.set_content(html)
    page.evaluate('(fixtures)=>{' + mock + '\n' + deps + '\n' + code('assets/profile-view.js') + '}', files)
    page.wait_for_selector('#profile .person-heading')
    assert page.locator('#profile h1').inner_text() == '[湖南湘鄉] 曾紀澤（劼剛）'
    page.select_option('#profile-select','person-zeng-guofan')
    page.wait_for_function("document.querySelector('#profile h1').textContent.includes('曾國藩')")
    assert '嘉慶十六年辛未' in page.locator('.person-heading').inner_text()
    page.select_option('#profile-select','person-guo-songtao')
    page.wait_for_function("document.querySelector('#profile h1').textContent.includes('郭嵩燾')")
    page.evaluate('history.back()')
    page.wait_for_function("document.querySelector('#profile h1').textContent.includes('曾國藩')")
    page.evaluate("location.hash='person-missing'")
    page.wait_for_selector('[role="alert"]')
    assert page.locator('#profile h1').inner_text() == 'Profile not found'
    browser.close()
print('Person navigation DOM integration passed.')
