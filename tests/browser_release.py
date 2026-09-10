"""Release acceptance on actual HTTP (local server or Pages); no network mocks.

Includes the published commit stamp when EXPECTED_COMMIT is set. The script
writes screenshots and a machine-readable report even when a check fails.
"""
from __future__ import annotations
import argparse, json, os, shutil, time
from pathlib import Path
from urllib.parse import urljoin, urldefrag
from playwright.sync_api import sync_playwright, expect

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--url',required=True)
p.add_argument('--output',type=Path,default=Path('build/release-browser'))
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
base=a.url.split('#')[0].split('?')[0]
report={'url':base,'mockedNetwork':False,'pageErrors':[],'failedRequests':[]}
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=os.environ.get('BROWSER_EXECUTABLE') or shutil.which('chromium') or shutil.which('google-chrome'),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1500,'height':1000},reduced_motion='reduce')
    page.set_default_timeout(45000)
    page.on('pageerror',lambda e:report['pageErrors'].append(str(e)))
    page.on('requestfailed',lambda r:report['failedRequests'].append({'url':r.url,'failure':r.failure}))
    def goto(path):
        target=urljoin(base,path)
        same_document=urldefrag(page.url)[0]==urldefrag(target)[0]
        response=page.goto(target,wait_until='networkidle',timeout=120000)
        # Fragment navigation has no document response. Do not hide a failed full navigation.
        if response is None:
            assert same_document,('Missing document response',path)
        else:
            assert response.status==200,(path,response.status)
        expect(page).to_have_url(target)
    def scroll_to(pid):
        page.locator('#reader').evaluate('''(r,id)=>{r.style.scrollBehavior='auto';const n=document.getElementById(id);r.scrollTop+=n.getBoundingClientRect().top-r.getBoundingClientRect().top-75;}''',pid)
        expect(page.locator('#reader p.active')).to_have_attribute('id',pid)
        page.wait_for_timeout(350)
    def self_label():return page.locator('[data-person-row="person-zeng-guofan"] .bar-name')
    try:
        expected=os.environ.get('EXPECTED_COMMIT')
        if expected:
            for attempt in range(12):
                r=page.request.get(urljoin(base,'deployment.json')+'?check='+str(time.time_ns()),timeout=45000)
                stamp=r.json() if r.status==200 else {}
                if stamp.get('commit')==expected:break
                time.sleep(10)
            assert stamp.get('commit')==expected,stamp
            report['deployment']=stamp
        goto('library.html')
        page.wait_for_selector('.collection-entry')
        report['biographies']=page.locator('.collection-entry').count()
        assert report['biographies']==809
        page.locator('#library-kind').select_option('all')
        expect(page.locator('.collection-entry')).to_have_count(815)
        page.locator('#library-search').fill('李鴻章')
        expect(page.locator('.collection-entry')).to_have_count(1)
        page.screenshot(path=str(a.output/'library.png'))
        page.locator('.collection-entry h2 a').click()
        page.wait_for_selector('#eccp-3643627-001')
        page.wait_for_selector('#reader-biography [data-profile-heading]')
        assert '李鴻章' in page.locator('#reader-biography').inner_text()
        assert page.locator('#reader p[id]').count()>10
        qsg=page.locator('#reader-biography .profile-source-navigation a')
        assert qsg.count()>0
        qsg.first.click()
        page.wait_for_selector('#reader-biography [data-profile-heading]')
        expect(page.locator('#reader-biography')).to_contain_text('李鴻章')
        assert 'person=person-li-hongzhang' in page.url
        assert page.locator('#reader p[id]').count()>5
        report['qsgCandidatePreservesPerson']=True
        goto('#eccp-zeng-guofan')
        page.wait_for_selector('#context-timeline [data-person-row]')
        page.wait_for_selector('#reader-biography .person-name-details')
        original=page.locator('#reader p[id]').all_text_contents()
        assert len(original)==17 and original[-1]=='Têng Ssŭ-yü'
        heading=page.locator('#reader-biography h1')
        assert heading.inner_text().strip()=='[湘鄉] 曾國藩'
        assert page.locator('#reader [data-profile-heading]').count()==0
        expect(page.locator('#reader-biography .person-ad')).to_have_text('[1811]–[1872]')
        expect(page.locator('#reader-biography .person-sui')).to_have_text('享年 62 歲')
        report['bracketedChineseLifeYears']=True
        for label in ['字伯涵','號滌生','諡文正']:
            assert label in page.locator('#reader-biography .person-name-details').inner_text()
        sizes=page.evaluate("[getComputedStyle(document.querySelector('#reader-biography h1')).fontSize,getComputedStyle(document.querySelector('#reader-biography .person-name-details')).fontSize]")
        assert float(sizes[1][:-2])<float(sizes[0][:-2])
        rects={name:page.locator('.'+name+'-panel').bounding_box() for name in ['text','biography','time','map']}
        assert abs(rects['text']['width']-2*rects['time']['width'])<4
        assert abs(rects['biography']['x']-rects['time']['x'])<2
        assert rects['biography']['y']+rects['biography']['height']<=rects['time']['y']+2
        assert rects['map']['y']>=rects['time']['y']+rects['time']['height']-2
        report['layout']=rects
        inside=self_label().evaluate('''n=>{const t=n.getBBox(),r=n.closest('[data-person-row]').querySelector('.life-bar').getBBox();return t.x>=r.x && t.x+t.width<=r.x+r.width+1;}''')
        assert inside
        assert page.locator('#context-timeline .paragraph-cursor').get_attribute('visibility')=='hidden'
        page.screenshot(path=str(a.output/'reader.png'))
        axis=page.locator('#context-timeline').get_attribute('data-axis')
        scroll_to('eccp-zeng-guofan-09')
        expect(page.locator('#year-label')).to_have_text('1865')
        cursor=page.locator('#context-timeline .paragraph-cursor');first=cursor.get_attribute('x1')
        assert cursor.get_attribute('visibility')=='visible'
        scroll_to('eccp-zeng-guofan-11')
        expect(page.locator('#year-label')).to_have_text('1867')
        assert cursor.get_attribute('x1')!=first
        expect(self_label()).to_contain_text('兩江總督')
        assert page.locator('#context-timeline').get_attribute('data-axis')==axis
        page.screenshot(path=str(a.output/'dated-timeline.png'))
        page.locator('#year').evaluate("n=>{n.value='1869';n.dispatchEvent(new Event('input',{bubbles:true}));}")
        expect(self_label()).to_contain_text('直隸總督')
        page.locator('#year').evaluate("n=>{n.value='1830';n.dispatchEvent(new Event('input',{bubbles:true}));}")
        expect(self_label()).to_have_text('曾國藩')
        page.locator('#follow').check()
        scroll_to('eccp-zeng-guofan-13')
        assert cursor.get_attribute('visibility')=='hidden'
        expect(self_label()).to_contain_text('大學士')
        report['datedNamesAndAnchor']=True
        page.locator('[data-set-locale="en"]').click()
        assert page.locator('#reader p[id]').all_text_contents()==original
        page.locator('[data-set-locale="zh-Hant"]').click()
        scroll_to('eccp-zeng-guofan-01')
        name=page.locator('#reader a[data-person-link]').first
        name.hover();page.wait_for_selector('#entity-card:not([hidden])')
        assert page.locator('#entity-card a').count()>=2
        expect(page.locator('#entity-card')).to_contain_text('[1811]–[1872]')
        expect(page.locator('#entity-card')).to_contain_text('享年 62 歲')
        page.keyboard.press('Escape')
        report['originalTextAndHoverPreserved']=True
        goto('#eccp-3633207')
        expect(page.locator('#source-family')).to_have_value('eccp')
        expect(page.locator('#source-group')).to_have_value('A')
        assert page.locator('#source-select option[value^="qsg"]').count()==0
        expect(page.locator('#eccp-3633207-003-n011')).to_have_attribute('data-entity','work-akedun-nianpu')
        expect(page.locator('#reader')).to_contain_text("S. K. Chang")
        assert page.locator('#reader [data-entity="person-eccp-3678153"]').count()==1
        assert page.locator('#reader [data-entity="person-hongli"]').count()==1
        page.locator('#source-family').select_option('qsg')
        page.locator('#source-group').select_option('accounts')
        page.locator('#source-select').select_option('qsg')
        page.wait_for_selector('#qsg-02')
        assert page.locator('#source-select option[value^="eccp"]').count()==0
        page.goto(urljoin(base,'#eccp-3642388'),wait_until='networkidle',timeout=120000)
        expect(page).to_have_url(base+'#eccp-3640793')
        page.wait_for_selector('#eccp-3640793-001')
        goto('review.html?source=eccp-3635454')
        page.wait_for_selector('.review-row')
        expect(page.locator('#review-results')).to_contain_text('san-yüan')
        page.screenshot(path=str(a.output/'editorial-review.png'))
        report['hierarchicalSourcesAndEditorialReview']=True
        goto('#eccp-zeng-guofan')
        page.wait_for_selector('#reader a[data-place-link]')
        loc=page.locator('#reader a[data-place-link]').first
        loc.hover();page.wait_for_selector('#entity-card:not([hidden])')
        expect(page.locator('#entity-card')).to_contain_text('地名')
        assert page.locator('#reader [data-type="place"]').first.evaluate('n=>getComputedStyle(n).borderBottomStyle')=='dotted'
        page.keyboard.press('Escape')
        page.locator('#reference-year').select_option('1911')
        page.locator('#reference-detail').select_option('county')
        for _ in range(4):page.locator('#context-zoom-in').click()
        visible=page.locator('#historical-reference-labels image[visibility="visible"]')
        expect(visible).to_have_count(1)
        expect(visible).to_have_attribute('data-label-level','county')
        expect(visible).to_have_attribute('data-label-year','1911')
        decoded=page.evaluate('''async()=>{const nodes=[...document.querySelectorAll('#historical-reference-labels image')];return Promise.all(nodes.map(n=>new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img.naturalWidth>0);img.onerror=reject;img.src=n.getAttribute('href');})));}''')
        assert decoded and all(decoded)
        page.screenshot(path=str(a.output/'place-labels.png'))
        page.locator('#reference-names').uncheck()
        expect(page.locator('#historical-reference-labels image[visibility="visible"]')).to_have_count(0)
        page.locator('#reference-names').check()
        page.locator('#reference-year').select_option('1820')
        expect(page.locator('#historical-reference-labels image[data-label-level="county"][visibility="visible"]')).to_have_count(0)
        report['placeLinksAndDatedMapNames']=True
        goto('places.html#place-region-hunan')
        page.wait_for_selector('.place-occurrence')
        expect(page.locator('#place-results')).to_contain_text('湖南')
        goto('places.html')
        page.locator('#place-mode').select_option('candidates')
        page.wait_for_selector('.place-candidate')
        assert page.locator('.place-candidate').count()<=60
        report['placeRecordsAndCandidateQueue']=True
        goto('profiles.html#person-zeng-guofan')
        page.wait_for_selector('#source-name-attestations')
        assert '1943' in page.locator('#source-name-attestations').inner_text()
        assert '字滌生' in page.locator('#profile').inner_text() and '號滌生' in page.locator('#profile').inner_text()
        assert page.locator('.source-name-group').count()>1
        assert '直隸總督' in page.locator('.dated-names').inner_text()
        report['sourceNameAttestations']=True
        expect(page.locator('#profile .person-ad')).to_have_text('[1811]–[1872]')
        expect(page.locator('#profile .life-grid')).to_contain_text('享年')
        assert '虛歲' not in page.locator('#profile .life-grid').inner_text()
        assert 'sui' not in page.locator('#profile .life-grid').inner_text()
        assert '中曆卒年' not in page.locator('#profile .life-grid').inner_text()
        goto('profiles.html#person-chonghou')
        page.wait_for_selector('#profile h1')
        expect(page.locator('#profile h1')).to_have_text('[完顏] 崇厚')
        assert '內務府鑲黃旗' in page.locator('#profile').inner_text()
        report['clanNotPlace']=True
        page.set_viewport_size({'width':390,'height':844})
        goto('#eccp-zeng-guofan');page.wait_for_selector('#historic-map')
        assert page.evaluate('document.documentElement.scrollWidth')<=391
        report['mobileNoOverflow']=True
        assert not report['pageErrors'],report['pageErrors']
        assert not report['failedRequests'],report['failedRequests']
        report['passed']=True
    except Exception as error:
        report['passed']=False;report['error']=str(error)
        page.screenshot(path=str(a.output/'failure.png'),full_page=True)
        raise
    finally:
        (a.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(report,ensure_ascii=False,indent=2));browser.close()
