import unittest,json,hashlib,copy
from pathlib import Path
from scripts.place_review import eligible_hits,leaf_ranges,rebase_text_occurrences
from scripts.renwen import TextIndex
ROOT=Path(__file__).resolve().parents[1]
class Places(unittest.TestCase):
    def test_does_not_mark_names_or_books(self):
        text='<p id="p"><span data-entity="person-test">Hunan</span> <i>Hunan gazetteer</i> 《湖南通志》 at Hunan</p>'
        plain,hits=eligible_hits(text,[('Hunan','place-test','province-expression'),('湖南','place-test','province-expression')],'en')
        self.assertEqual(len(hits),1)
        self.assertEqual(plain[hits[0][0]:hits[0][1]],'Hunan')
    def test_source_scoped_native_forms(self):
        rules=[('Foo','place-test','local-native')]
        self.assertEqual(len(eligible_hits('<p>Foo said this. He went to Foo.</p>',rules,'en')[1]),1)
    def test_word_boundaries(self):
        self.assertEqual(len(eligible_hits('<p>Hunanese. Hunan. NotHunan.</p>',[('Hunan','place-test','province-expression')],'en')[1]),1)
    def test_ambiguous_reference_not_auto_linked(self):
        self.assertEqual(eligible_hits('<p>in Foo</p>',[('Foo','place-a','local-native'),('Foo','place-b','local-native')],'en')[1],[])
    def test_exact_html_entities_and_formatting(self):
        text='<p><i>book</i> &amp; to Hunan.</p>';plain,hits=eligible_hits(text,[('Hunan','place-a','province-expression')],'en')
        self.assertEqual(plain,'book & to Hunan.');a,b,x,y,*_=hits[0];self.assertEqual(text[x:y],'Hunan')
    def test_protected_chinese_titles(self):
        self.assertEqual(len(eligible_hits('<p>《湖南通志》與湖南。</p>',[('湖南','place-a','province-expression')],'zh')[1]),1)
    def test_zhili_administrative_adjective(self):
        self.assertEqual(len(eligible_hits('<p>升直隸州。直隸總督。</p>',[('直隸','place-a','province-expression')],'zh')[1]),1)
    def test_manifest_and_no_invented_coordinates(self):
        c=json.loads((ROOT/'data/catalog.json').read_text());entities={e['id']:e for e in c['entities']};ms={m['id']:m for m in c['mentions']}
        for p in json.loads((ROOT/'data/places.json').read_text())['records']:
            self.assertEqual(entities[p['id']]['type'],'place')
            if p['kind']!='existing-reference-place':self.assertFalse(entities[p['id']].get('point'))
            for ref in p['evidence']:
                self.assertEqual(ms[ref['mention']]['entity'],p['id']);self.assertEqual(ms[ref['mention']]['quote'],ref['quote'])
        report=json.loads((ROOT/'data/editorial/place-pass.json').read_text());self.assertEqual(report['eccpBiographiesScanned'],809)
        self.assertEqual(report['newPlaceMentions'],sum(m.get('origin')==report['version'] for m in ms.values()))
    def test_names_pin_to_matching_boundary_sources(self):
        manifest=json.loads((ROOT/'data/reference-maps.json').read_text());layers={(r['year'],r['level']):r for r in manifest['layers']}
        self.assertGreaterEqual(len(manifest['labelLayers']),5)
        for r in manifest['labelLayers']:
            self.assertEqual(r['sourceSha256'],layers[r['year'],r['level']]['sourceSha256'])
            self.assertEqual(r['bbox'],manifest['bbox']);self.assertGreater(r['labelCount'],0)
            self.assertEqual(hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest(),r['sha256'])
            self.assertLessEqual(r['labelCount'],r['candidateCount'])
        self.assertFalse(any(r['year']==1820 and r['level']=='county' for r in manifest['labelLayers']))

    def test_markup_only_rebases_exact_quotation_anchors(self):
        data={'occurrences':[{'id':'occ-test','witness':'w','sourceSha256':'old','selectors':[{'passage':'p','start':0,'end':5,'exact':'Hunan'}]}]}
        original=copy.deepcopy(data['occurrences'][0]['selectors'])
        self.assertEqual(rebase_text_occurrences(data,{'w':('old','new',{'p':'Hunan.'},{'p':'Hunan.'})}),['occ-test'])
        self.assertEqual(data['occurrences'][0]['sourceSha256'],'new')
        self.assertEqual(data['occurrences'][0]['selectors'],original)
    def test_rebase_refuses_stale_or_changed_quotation(self):
        data={'occurrences':[{'id':'occ-test','witness':'w','sourceSha256':'old','selectors':[{'passage':'p','start':0,'end':5,'exact':'Hunan'}]}]}
        for change in [('other','new',{'p':'Hunan.'},{'p':'Hunan.'}),('old','new',{'p':'Hunan.'},{'p':'Honan.'}),('old','new',{'p':'Honan.'},{'p':'Honan.'})]:
            with self.assertRaises(ValueError): rebase_text_occurrences(data,{'w':change})
        self.assertEqual(data['occurrences'][0]['sourceSha256'],'old')
