"""Exercise a real HTTP-served reader (local server or Pages), with no mocked fetches.

python tests/browser_live.py --url http://127.0.0.1:8000/ --output build/browser
"""
from __future__ import annotations
import argparse, json, os, shutil
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url',required=True)
parser.add_argument('--output',type=Path,default=Path('build/browser'))
a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=True)
report={'url':a.url,'mockedNetwork':False,'pageErrors':[],'failedRequests':[]}
with sync_playwright() as p:
    executable=os.environ.get('BROWSER_EXECUTABLE') or shutil.which('chromium') or shutil.which('google-chrome')
    browser=p.chromium.launch(headless=True,executable_path=executable,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1500,'height':1000},reduced_motion='reduce')
    page.set_default_timeout(15000)
    page.on('pageerror',lambda e:report['pageErrors'].append(str(e)))
    page.on('requestfailed',lambda r:report['failedRequests'].append({'url':r.url,'failure':r.failure}))
    try:
        response=page.goto(a.url,wait_until='networkidle',timeout=60000)
        assert response.status==200,response.status
        page.wait_for_selector('#eccp-zeng-guofan-01')
        page.wait_for_selector('#historic-map')
        assert page.locator('#reader p[id]').count()==17
        assert page.locator('#reader p[id]').last.inner_text()=='Têng Ssŭ-yü'
        report['completeEntryParagraphs']=17
        # All image resources must actually be served and decode, not just have DOM nodes.
        layers=page.locator('#historical-reference-images image')
        assert layers.count()==5
        paths=layers.evaluate_all('(nodes)=>nodes.map(n=>n.getAttribute("href"))')
        decoded=page.evaluate('''async paths=>Promise.all(paths.map(path=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve({path,width:im.naturalWidth,height:im.naturalHeight});im.onerror=()=>reject(new Error('Image failed: '+path));im.src=path;})))''',paths)
        assert all(i['width']==3000 and i['height']==2200 for i in decoded)
        report['decodedHistoricalLayers']=decoded
        m=page.locator('#historic-map');before=m.get_attribute('viewBox');b=m.bounding_box();x=b['x']+b['width']*.5;y=b['y']+b['height']*.45
        page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+45,y+20,steps=8);page.mouse.up()
        after=m.get_attribute('viewBox');assert after!=before
        report['drag']={'before':before,'after':after}
        before=after;page.mouse.move(x,y);page.mouse.wheel(0,-250);page.wait_for_timeout(300);assert m.get_attribute('viewBox')!=before
        report['wheelZoom']=m.get_attribute('viewBox')
        for _ in range(4):page.locator('#context-zoom-in').click()
        assert page.locator('[data-reference-year="1911"][data-reference-level="county"]').get_attribute('visibility')=='visible'
        report['countyVisibleAfterZoom']=True
        page.screenshot(path=str(a.output/'county-map.png'))
        page.locator('#reference-year').select_option('1820')
        assert '無縣界' in page.locator('#reference-map-status').inner_text()
        report['noInvented1820CountyLayer']=True
        page.locator('#context-world').click();before=m.get_attribute('viewBox');m.focus();page.keyboard.press('ArrowRight');assert m.get_attribute('viewBox')!=before
        report['overviewPanUnlocked']=True
        page.locator('#context-map-home').click();page.locator('#reference-year').select_option('1911');page.locator('#context-zoom-in').click()
        page.screenshot(path=str(a.output/'reader.png'))
        page.locator('#reader a[data-person-link]').first.hover();page.wait_for_selector('#entity-card:not([hidden])');assert page.locator('#entity-card a').count()>=2;page.keyboard.press('Escape')
        report['hoverDestinations']=True
        page.evaluate("w=>window.dispatchEvent(new CustomEvent('renwen:navigate',{detail:{witness:w}}))",'qsg');page.wait_for_selector('#qsg-02');assert page.locator('#reader p[id]').count()==4
        page.locator('[data-unit-occurrence="occ-qsg-yili-memorial"]').click();page.wait_for_selector('.unit-reading')
        original=page.locator('.unit-reading').inner_text();assert '伊犁一役' in original
        assert page.locator('.unit-breadcrumb a').count()==1
        page.locator('[data-set-locale="en"]').click();assert page.locator('.unit-reading').inner_text()==original
        report['quotationContextAndLanguagePreserved']=True
        page.screenshot(path=str(a.output/'quotation.png'),full_page=True)
        mobile=browser.new_page(viewport={'width':390,'height':844},has_touch=True,is_mobile=True,reduced_motion='reduce')
        mobile.on('pageerror',lambda e:report['pageErrors'].append(str(e)))
        mobile.goto(a.url,wait_until='networkidle',timeout=60000);mobile.wait_for_selector('#historic-map')
        assert mobile.evaluate('document.documentElement.scrollWidth')<=391
        report['mobileNoOverflow']=True
        assert not report['pageErrors'],report['pageErrors']
        assert not report['failedRequests'],report['failedRequests']
        report['passed']=True
    except Exception as e:
        report['passed']=False;report['error']=str(e)
        page.screenshot(path=str(a.output/'failure.png'),full_page=True)
        raise
    finally:
        (a.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(report,ensure_ascii=False,indent=2))
        browser.close()
