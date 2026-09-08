"""Optional real-browser smoke checks. Requires Playwright and a Chromium executable.
Run a local server first, then: python tests/browser_smoke.py http://127.0.0.1:8000
Set CHROMIUM_EXECUTABLE when needed. Screenshots are optional via RENWEN_SCREENSHOT.
"""
import json
import re
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000'
with sync_playwright() as p:
    kwargs={'headless':True}
    if os.getenv('CHROMIUM_EXECUTABLE'):kwargs['executable_path']=os.environ['CHROMIUM_EXECUTABLE']
    browser=p.chromium.launch(**kwargs)
    page=browser.new_page(viewport={'width':1600,'height':1050})
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    if os.getenv('RENWEN_OFFLINE') == '1':
        # Render local fixtures in memory when HTTP navigation is unavailable.
        # This checks UI behavior, not HTTP loading or deployment.
        root=Path(__file__).resolve().parents[1]
        html=(root/'index.html').read_text(encoding='utf-8')
        html=re.sub(r'<link[^>]+>', '', html)
        html=re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S)
        land=(root/'assets/land.svg').read_text(encoding='utf-8')
        path=re.search(r'<path .*?</svg>',land).group(0).removesuffix('</svg>')
        html=html.replace('<image href="assets/land.svg" width="170" height="80"/>',path)
        fixtures={str(f.relative_to(root)):f.read_text(encoding='utf-8')
                  for f in (root/'data').rglob('*') if f.suffix in ('.json','.html')}
        core=(root/'assets/core.js').read_text(encoding='utf-8').replace('export ', '')
        app=(root/'assets/app.js').read_text(encoding='utf-8').split('\n',1)[1]
        script='const fixtureFiles='+json.dumps(fixtures,ensure_ascii=False)+';'
        script+='window.fetch=async u=>new Response(fixtureFiles[String(u)]||"",{status:fixtureFiles[String(u)]?200:404});'
        script+=core+'\nconst h=escapeHTML;\n'+app
        page.set_content(html)
        page.add_style_tag(content=(root/'assets/style.css').read_text(encoding='utf-8'))
        page.add_script_tag(content=script,type='module')
    else:
        page.goto(url)
    page.wait_for_selector('#eccp-01')
    assert page.locator('.panel').count()==3
    assert page.locator('#reader [data-entity]').count()>20
    page.locator('#eccp-01-m01').click();assert page.locator('#inspector').is_visible()
    page.locator('#candidate').select_option('person-zeng-guofan')
    page.locator('#reason').fill('Synthetic browser test; not a historical identification.')
    page.locator('#propose').click();assert page.locator('#queue-count').inner_text()=='1'
    page.locator('#close-inspector').click()
    page.locator('#queue-button').click()
    with page.expect_download() as d:page.locator('#export-queue').click()
    assert 'relink-mention' in Path(d.value.path()).read_text()
    page.locator('#close-dialog').click()
    page.locator('#source-select').select_option('qsg');page.wait_for_selector('#qsg-01')
    before=page.locator('#qsg-01').text_content();page.locator('#punctuation').check()
    assert page.locator('#reader .editorial-punctuation.hidden-mark').count()>5
    assert page.locator('#qsg-01').text_content()==before
    assert '，' not in page.locator('#qsg-01').inner_text()
    page.locator('#source-select').select_option('eccp');page.wait_for_selector('#eccp-01')
    page.locator('#reader').evaluate('(n)=>n.scrollTop=520');page.wait_for_timeout(300)
    assert 'eccp-' in page.locator('#reading-context').inner_text()
    raw=b'<?xml version="1.0"?><synthetic future="keep"><span test="unknown">abc</span></synthetic>'
    page.locator('#xml-file').set_input_files({'name':'synthetic.xml','mimeType':'application/xml','buffer':raw})
    page.wait_for_selector('#xml-export')
    with page.expect_download() as d:page.locator('#xml-export').click()
    assert Path(d.value.path()).read_bytes()==raw
    page.locator('#close-dialog').click()
    page.locator('#reader').evaluate('(n)=>n.scrollTop=0');page.wait_for_timeout(300)
    if os.getenv('RENWEN_SCREENSHOT'):page.screenshot(path=os.environ['RENWEN_SCREENSHOT'],full_page=True)
    assert not errors,errors
    # Small-screen layout remains usable without horizontal body overflow.
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
    browser.close()
print('Browser smoke checks passed (desktop, mobile, source switch, punctuation, proposals, XML).')
