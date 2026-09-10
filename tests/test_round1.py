"""Small structural tests; whole-inventory audit runs once in round1_validate."""
import json,unittest
from pathlib import Path
from scripts.round1_import import reading_blocks,NameMatcher
from scripts.profiles import validate_profile,canonical_name
ROOT=Path(__file__).resolve().parents[1]
class RoundOne(unittest.TestCase):
    def test_loose_page_continuation_is_not_dropped(self):
        html='<div class="prp-pages-output"><p>Beginning.</p>Loose <i>continuation</i>.<div><p>End.</p></div></div>'
        blocks,whole=reading_blocks(html)
        self.assertEqual(''.join(n.text() for n in blocks),'Beginning.Loose continuation.End.')
        self.assertEqual(whole,'Beginning.Loosecontinuation.End.')
    def test_table_text_and_footer_byline_are_preserved(self):
        bs,_=reading_blocks('<div class="prp-pages-output"><p>A</p><table><tr><td>B</td><td>C</td></tr></table><div><p>Author</p></div></div>')
        self.assertEqual([n.text() for n in bs],['A','B','C','Author'])
    def test_multiple_transclusion_bodies(self):
        bs,_=reading_blocks('<div class="prp-pages-output"><p>A</p></div><div class="prp-pages-output"><p>B</p></div>')
        self.assertEqual([n.text() for n in bs],['A','B'])
    def test_matcher_overlapping_terms_and_han(self):
        hits=list(NameMatcher(['曾國藩','國藩','tsêng kuo-fan']).find('曾國藩 Tsêng Kuo-fan'))
        self.assertIn((0,3,'曾國藩'),hits);self.assertIn((1,3,'國藩'),hits);self.assertIn((4,17,'tsêng kuo-fan'),hits)
    def test_full_inventory_and_types(self):
        c=json.loads((ROOT/'data/collections/eccp.json').read_text())
        self.assertEqual(c['counts']['biography'],809);self.assertEqual(c['counts']['cross-reference'],193);self.assertEqual(c['counts']['reference-material'],6)
        self.assertEqual(len(c['entries']),1008)
    def test_clan_and_registry_are_independent(self):
        p=json.loads((ROOT/'data/people/person-chonghou.json').read_text());validate_profile(p)
        self.assertEqual(canonical_name(p),'[完顏] 崇厚');self.assertIsNone(p['name']['surname']);self.assertTrue(p['name']['registration']['attestations'])
    def test_county_without_invented_registration(self):
        p=json.loads((ROOT/'data/people/person-zeng-jize.json').read_text());self.assertEqual(canonical_name(p),'[湘鄉] 曾紀澤')
        self.assertNotIn('民籍',p['name'].get('registration',{}).get('administrativeLabel',''))
if __name__=='__main__':unittest.main()
