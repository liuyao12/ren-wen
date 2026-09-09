"""Exercise the full collection through an actual HTTP server; no fetch mocks."""
import argparse,json,os,shutil,time
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--output',type=Path,default=Path('build/round1-browser'));a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
report={'mockedNetwork':False,'url':a.url,'pageErrors':[],'failedRequests':[]};base=a.url.split('#')[0].split('?')[0]
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=os.environ.get('BROWSER_EXECUTABLE') or shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
    page=b.new_page(viewport={'width':1500,'height':1000},reduced_motion='reduce');page.set_default_timeout(60000)
    page.on('pageerror',lambda e:report['pageErrors'].append(str(e)));page.on('requestfailed',lambda r:report['failedRequests'].append(r.url));requests=[];page.on('request',lambda r:requests.append(r.url))
    try:
        assert page.goto(urljoin(base,'library.html'),wait_until='networkidle',timeout=120000).status==200
        page.wait_for_selector('.collection-entry');report['biographies']=page.locator('.collection-entry').count();assert report['biographies']==809
        page.locator('#library-search').fill('李鴻章');assert page.locator('.collection-entry').count()==1
        page.screenshot(path=str(a.output/'library.png'))
        page.locator('.collection-entry h2 a').click();page.wait_for_selector('#eccp-3643627-001');page.wait_for_selector('#historic-map');page.wait_for_selector('#reader a[data-person-link]')
        report['liParagraphs']=page.locator('#reader p[id]').count();assert report['liParagraphs']>10;assert '李鴻章' in page.locator('[data-profile-heading]').inner_text()
        page.locator('#reader a[data-person-link]').first.hover();page.wait_for_selector('#entity-card:not([hidden])');assert page.locator('#entity-card a').count()>=2;page.keyboard.press('Escape')
        qsg=page.locator('[data-profile-heading] .profile-source-navigation a');assert qsg.count()>0;qsg.first.click();page.wait_for_selector('#historic-map');page.wait_for_selector('[data-profile-heading]');page.wait_for_timeout(800)
        report['qsgUrl']=page.url;assert 'person=person-li-hongzhang' in page.url;assert '李鴻章' in page.locator('[data-profile-heading]').inner_text();assert page.locator('#reader p[id]').count()>5
        assert page.goto(urljoin(base,'profiles.html#person-chonghou'),wait_until='networkidle',timeout=120000).status==200
        page.wait_for_selector('#profile h1');assert '[完顏] 崇厚（地山）' in page.locator('#profile h1').inner_text();assert '內務府鑲黃旗' in page.locator('#profile').inner_text();page.screenshot(path=str(a.output/'wanyan-profile.png'))
        page.locator('[data-set-locale="en"]').click();assert '完顏' in page.locator('#profile h1').inner_text()
        page.goto(base+'#eccp-zeng-guofan',wait_until='networkidle',timeout=120000);page.wait_for_selector('#historic-map');page.wait_for_selector('[data-profile-heading]');assert page.locator('#reader p[id]').count()==17
        assert '[湘鄉]' in page.locator('[data-profile-heading]').inner_text();page.screenshot(path=str(a.output/'reader.png'))
        report['profileFileRequests']=len([u for u in requests if '/data/people/person-' in u]);assert report['profileFileRequests']<10,report
        report['passed']=not report['pageErrors'] and not report['failedRequests'];assert report['passed'],report
    finally:
        (a.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));b.close()
print(json.dumps(report,ensure_ascii=False,indent=2))
