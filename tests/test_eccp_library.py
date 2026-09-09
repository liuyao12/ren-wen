"""Corpus completeness and annotation mechanics; no synthetic claims are published."""
import hashlib,json,re,sqlite3,tempfile,unittest
from pathlib import Path
from scripts.eccp_batch import source_paragraphs,Tree,annotate
from scripts.works import load_works,index_db
from scripts.renwen import build_db
ROOT=Path(__file__).resolve().parents[1]

class ECCPLibraryTest(unittest.TestCase):
    def setUp(self):
        self.c=json.loads((ROOT/'data/catalog.json').read_text());self.works=load_works(ROOT)
    def test_five_complete_eccp_entries(self):
        self.assertEqual({s['id'] for s in self.c['sources'] if s.get('complete') and s['id'] in {'eccp','eccp-chonghou','eccp-dong-xun','eccp-guo-songtao','eccp-zeng-guofan'}},{'eccp','eccp-chonghou','eccp-dong-xun','eccp-guo-songtao','eccp-zeng-guofan'})
    def test_raw_content_is_complete(self):
        # Compare all characters, allowing only display whitespace and new reading breaks.
        for s in self.c['sources']:
            if s['id'] not in {'eccp','eccp-chonghou','eccp-dong-xun','eccp-guo-songtao','eccp-zeng-guofan'}:continue
            raw=(ROOT/s['rawResponse']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),s['rawSha256'])
            source=''.join(n.text() for n in source_paragraphs(json.loads(raw)['parse']['text']['*']))
            upstream=Tree((ROOT/s['upstream']).read_text()).root.text()
            normalize=lambda text:re.sub(r'\s+','',text)
            self.assertEqual(normalize(source),normalize(upstream),s['id'])
            self.assertTrue(upstream.rstrip().endswith('Têng Ssŭ-yü' if s['id']=='eccp-zeng-guofan' else 'Tu Lien-chê'))
    def test_people_and_work_destinations_exist(self):
        people={json.loads((ROOT/'data/people'/f).read_text())['id'] for f in json.loads((ROOT/'data/people/index.json').read_text())['profiles']}
        works={w['id'] for w in self.works}
        for m in self.c['mentions']:
            if m['entity'].startswith('person-'):self.assertIn(m['entity'],people)
            if m['entity'].startswith('work-'):self.assertIn(m['entity'],works)
        self.assertGreaterEqual(len(people),70);self.assertGreaterEqual(len(works),45)
    def test_bibliographies_and_byline_annotated(self):
        ms=self.c['mentions']
        for s in self.c['sources']:
            if s.get('complete') and s['id'] in {'eccp','eccp-chonghou','eccp-dong-xun','eccp-guo-songtao','eccp-zeng-guofan'}:
                self.assertTrue(any(m['witness']==s['id'] and m['entity']==('person-teng-ssu-yu' if s['id']=='eccp-zeng-guofan' else 'person-tu-lien-che') for m in ms))
                self.assertTrue(any(m['witness']==s['id'] and m['entity'].startswith('work-') for m in ms))
    def test_legacy_mention_ids_retained(self):
        ids={m['id'] for m in self.c['mentions']}
        for mid in ['eccp-01-m01','eccp-03-m01','eccp-04-m01','eccp-08-m05','eccp-15-m02','qsg-01-m01']:
            self.assertIn(mid,ids)
    def test_source_errors_not_silently_repaired(self):
        t=Tree((ROOT/'data/upstream/eccp-dong-xun.html').read_text()).root.text()
        self.assertIn('in 1992',t)
        self.assertIn('co mpleted',t)
    def test_work_does_not_turn_into_person(self):
        n=Tree('<i>Author Wang collected works</i>').root
        rules=[{'entity':'work-test','terms':['Author Wang collected works'],'witness':'test'}, {'entity':'person-test','terms':['Wang'],'witness':'test'}]
        html,ms=annotate(n,rules,'test-01',[])
        self.assertEqual([m['entity'] for m in ms],['work-test']);self.assertIn('<i>',html)
    def test_work_sqlite(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'db.sqlite';build_db(path);index_db(path);index_db(path)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM work_profiles').fetchone()[0],len(self.works))
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
    def test_editorial_names_are_typed(self):
        p=json.loads((ROOT/'data/people/person-hongli.json').read_text())
        self.assertNotIn('龍翰',[n['value'] for n in p['name']['zi']])
        self.assertTrue(all(p['reviewStatus']=='agent-proposed' for p in self.works))
