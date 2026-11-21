"""Verify Six Dynasties reader navigation and person citations over HTTP."""

import os
import re
import shutil
import sys
from urllib.parse import parse_qs, quote, urlencode, urljoin, urlsplit

from playwright.sync_api import expect, sync_playwright


base = sys.argv[1]
chapter = "c-jinshu-065-wangdao-family"


def follow_citation(page, evidence, anchor, text):
    expect(evidence).to_have_count(1, timeout=45000)
    evidence.locator("summary").first.click()
    link = evidence.locator(f'a[href*="passage={quote(anchor, safe="")}"]')
    expect(link).to_have_count(1)
    link.click()
    expect(page.locator(f'[id="{anchor}"]')).to_contain_text(text, timeout=45000)
    assert parse_qs(urlsplit(page.url).fragment).get("passage") == [anchor], page.url


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path=os.environ.get("BROWSER_EXECUTABLE") or shutil.which("chromium") or shutil.which("google-chrome"),
        args=["--no-sandbox"],
    )
    for width in (390, 1440):
        page = browser.new_page(viewport={"width": width, "height": 900})
        route = urlencode({"work": "w-jinshu", "book": "b-jinshu-065", "chapter": chapter})
        page.goto(urljoin(base, "reader.html#" + route))
        article = page.locator(f'article[data-chapter-id="{chapter}"]')
        delivered = page.request.get(urljoin(base, "data/corpus/jinshu/065.json")).json()
        paragraphs = delivered["paragraphs"]
        expect(article.locator("[data-source-text]")).to_have_count(len(paragraphs), timeout=45000)
        links = [link for paragraph in paragraphs for mention in paragraph["mentions"]
                 for link in mention.get("editorial_biographies", [])]
        reviewed = delivered.get("annotation", {}).get("status") == "reviewed"
        if not reviewed:
            assert len(links) == 16, "The Ren-Wen pilot must retain its verified biography links."
            expect(page.locator(f'[id="{chapter}:p001:m0058"]')).to_have_text("此兒")
        first = article.locator("[data-source-text]").first
        expect(first).to_contain_text("此兒")
        expect(first.locator("a").filter(has_text=re.compile(r"^此兒$"))).to_have_count(0)
        cross_links = article.locator("[data-editorial-biographies] a")
        expect(cross_links).to_have_count(len(links))
        link = cross_links.filter(has_text="〈王弘〉")
        if any("〈王弘〉" in link_data["label"] for link_data in links):
            expect(link).to_have_count(1)
            link.click()
        else:
            hong = urlencode({"work": "w-songshu", "book": "b-songshu-042", "chapter": "c-songshu-042-wanghong"})
            page.goto(urljoin(base, "reader.html#" + hong))
        expect(page.locator('[id="c-songshu-042-wanghong:p001"]')).to_contain_text("父珣，司徒", timeout=45000)
        page.goto(urljoin(base, "person.html#7r6_k52_qji_ABAAAA"))
        life = page.locator(".person-life-summary")
        expect(life).to_contain_text("隆安四年", timeout=45000)
        expect(life).to_contain_text("400")
        expect(page.get_by_text("正在載入家族關係…", exact=True)).to_have_count(0, timeout=45000)
        quotation = page.locator("blockquote").filter(has_text="東亭侯王珣卒")
        evidence = life.locator("details").filter(has=quotation)
        follow_citation(page, evidence, "c-jinshu-010-wangxun-longan4:p001", "東亭侯王珣卒")
        page.goto(urljoin(base, "person.html#e43_8c2_c4d"))
        family = page.locator("details").filter(has=page.locator("blockquote").filter(has_text="謐從弟諶"))
        evidence = family.filter(has=page.locator("summary").filter(has_text="來源與關係原詞"))
        follow_citation(page, evidence, f"{chapter}:line102", "謐從弟諶")

        epitaphs = (
            ("ih5_w5y_2s0", "c-epitaph-cuihun-excerpts:p001", "元象元年二月五日奄至物故",
             ("https://guji.10huan.com/Article/7147_7165.html",)),
            ("30f_353_0e8", "c-epitaph-cuihong-excerpts:p001", "廿九日庚午薨",
             ("https://www.sohu.com/a/259439652_258370", "https://www.sohu.com/a/260163234_770283")),
        )
        for person, anchor, text, sources in epitaphs:
            page.goto(urljoin(base, "person.html#" + person))
            evidence = page.locator(".person-life-summary details").filter(
                has=page.locator("blockquote").filter(has_text=text)
            ).first
            follow_citation(page, evidence, anchor, text)
            source_links = ", ".join(f'a[href="{source}"]' for source in sources)
            expect(page.locator(source_links).first).to_be_visible()
        print(f"六朝人物引文驗證通過，視窗寬度 {width}px。", flush=True)
        page.close()
    browser.close()
