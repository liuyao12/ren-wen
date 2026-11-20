"""Verify the Ren-Wen pilot in the actual staged or published reader."""

import os
import shutil
import sys
from urllib.parse import urlencode, urljoin

from playwright.sync_api import expect, sync_playwright


base = sys.argv[1]
chapter = "c-jinshu-065-wangdao-family"
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
        expect(article.locator("[data-source-text]")).to_have_count(45, timeout=45000)
        expect(article.locator("[data-editorial-biographies] a")).to_have_count(16)
        expect(page.locator(f'[id="{chapter}:p001:m0058"]')).to_have_text("此兒")
        expect(page.locator(f'a[id="{chapter}:p001:m0058"]')).to_have_count(0)
        link = article.locator("[data-editorial-biographies] a").filter(has_text="〈王弘〉")
        expect(link).to_have_count(1)
        link.click()
        expect(page.locator('[id="c-songshu-042-wanghong:p001"]')).to_contain_text("父珣，司徒", timeout=45000)
        page.goto(urljoin(base, "person.html#7r6_k52_qji_ABAAAA"))
        life = page.locator(".person-life-summary")
        expect(life).to_contain_text("隆安四年", timeout=45000)
        expect(life).to_contain_text("400")
        quotation = page.locator("blockquote").filter(has_text="東亭侯王珣卒")
        evidence = life.locator("details").filter(has=quotation)
        expect(evidence).to_have_count(1)
        evidence.locator("summary").first.click()
        evidence.locator('a[href*="c-jinshu-010-wangxun-longan4"]').click()
        passage = page.locator('[id="c-jinshu-010-wangxun-longan4:p001"]')
        expect(passage).to_contain_text("東亭侯王珣卒", timeout=45000)
        page.goto(urljoin(base, "person.html#e43_8c2_c4d"))
        family = page.locator("details").filter(has=page.locator("blockquote").filter(has_text="謐從弟諶"))
        expect(family.filter(has=page.locator("summary").filter(has_text="來源與關係原詞"))).to_have_count(1, timeout=45000)
        page.close()
    browser.close()
