import copy,hashlib,json,sqlite3,tempfile,unittest
from pathlib import Path
from scripts.text_units import load_units,validate_units,index_db
from scripts.import_entry import complete_paragraphs,compact
from scripts.renwen import TextIndex,build_db
from scripts.eccp_batch import Tree,clean,nodes
ROOT=Path(__file__).resolve().parents[1]
class TextUnitsTest(unittest.TestCase):
 def setUp(self):
  self.c=json.loads((ROOT/'data/catalog.json').read_text());self.d=load_units(ROOT);self.ps={}
  for s in self.c['sources']:self.ps.update({(s['id'],p):t for p,t in TextIndex((ROOT/s['text']).read_text()).passages.items()})
 def test_complete_zeng_source_including_bibliography_and_author(self):
  s=next(s for s in self.c['sources'] if s['id']=='eccp-zeng-guofan');raw=(ROOT/s['rawResponse']).read_bytes();ps,full=complete_paragraphs(json.loads(raw)['parse']['text']['*']);self.assertEqual(len(ps),17);self.assertEqual(ps[-1].text(),'Têng Ssŭ-yü');self.assertEqual(compact(''.join(self.ps[s['id'],f'{s["id"]}-{i:02}'] for i in range(1,18))),full)
 def test_unrepresented_block_content_is_rejected(self):
  with self.assertRaisesRegex(ValueError,'Unrepresented'):complete_paragraphs('<div class="prp-pages-output"><p>Text.</p><blockquote>Must not vanish.</blockquote></div>')
 def test_quotation_is_in_parent_and_in_its_own_record(self):
  q=next(o for o in self.d['occurrences'] if o['role']=='quotation');self.assertEqual(q['container'],'occ-qsg');self.assertIn('伊犁一役',q['selectors'][0]['exact']);self.assertIn(q['selectors'][0]['exact'],self.ps['qsg','qsg-02'])
 def test_complete_qsg_account_has_no_missing_memorial(self):
  source=next(s for s in self.c['sources'] if s['id']=='qsg');p=json.loads((ROOT/source['rawResponse']).read_text())['parse'];ns=[clean(n).text().strip() for n in nodes(Tree(p['text']['*']).root) if n.tag=='p'];a=next(i for i,t in enumerate(ns) if t.startswith('曾紀澤，'));b=next(i for i in range(a+1,len(ns)) if ns[i].startswith('薛福成，'));self.assertEqual(compact(''.join(ns[a:b])),compact(''.join(self.ps['qsg',f'qsg-{i:02}'] for i in range(1,5))))
 def test_invalid_range_rejected(self):
  d=copy.deepcopy(self.d);d['occurrences'][-1]['selectors'][0]['end']+=10000
  with self.assertRaisesRegex(ValueError,'range'):validate_units(d,self.c,self.ps)
 def test_changed_text_needs_review(self):
  d=copy.deepcopy(self.d);d['occurrences'][-1]['selectors'][0]['exact']='Different text'
  with self.assertRaisesRegex(ValueError,'differs'):validate_units(d,self.c,self.ps)
 def test_stale_revision_rejected(self):
  d=copy.deepcopy(self.d);d['occurrences'][0]['sourceSha256']='0'*64
  with self.assertRaisesRegex(ValueError,'Stale'):validate_units(d,self.c,self.ps)
 def test_cross_witness_containment_rejected(self):
  d=copy.deepcopy(self.d);d['occurrences'][-1]['container']='occ-qsg'
  with self.assertRaisesRegex(ValueError,'same witness'):validate_units(d,self.c,self.ps)
 def test_containment_does_not_turn_quote_into_independent_evidence(self):
  q=next(o for o in self.d['occurrences'] if o['role']=='quotation');self.assertEqual(q['witness'],'qsg');self.assertEqual(len([o for o in self.d['occurrences'] if o['unit']==q['unit']]),1)
 def test_same_unit_accepts_distinct_readings_without_merging(self):
  d=copy.deepcopy(self.d);o=copy.deepcopy(d['occurrences'][-1]);o['id']='occ-test-second-reading';o['unit']='text-zeng-jize-yili-memorial';o['role']='excerpt';o['readingType']='variant-reading';d['occurrences'].append(o);validate_units(d,self.c,self.ps);self.assertNotEqual(o['selectors'][0]['exact'],next(x for x in d['occurrences'] if x['id']=='occ-qsg-yili-memorial')['selectors'][0]['exact'])
 def test_code_point_offsets_not_utf16(self):
  c={'sources':[{'id':'s','sha256':'a'}]};d={'schemaVersion':1,'units':[{'id':'text-test','title':'test','kind':'quotation'}],'occurrences':[{'id':'occ-test','unit':'text-test','witness':'s','role':'quotation','readingType':'quoted-reading','sourceSha256':'a','selectors':[{'passage':'p','start':1,'end':3,'exact':'𠀀文'}]}]};validate_units(d,c,{('s','p'):'甲𠀀文乙'})
 def test_sqlite_derived_layers(self):
  with tempfile.TemporaryDirectory() as tmp:
   db=Path(tmp)/'test.sqlite';build_db(db);index_db(db);index_db(db)
   with sqlite3.connect(db) as conn:self.assertEqual(conn.execute('select count(*) from text_units').fetchone()[0],len(self.d['units']))
 def test_boundary_images_are_cropped_dated_and_hashed(self):
  m=json.loads((ROOT/'data/reference-maps.json').read_text());self.assertEqual(m['bbox'],[108,24,123,35]);self.assertEqual({l['year'] for l in m['layers']},{1820,1911});self.assertFalse(any(l['year']==1820 and l['level']=='county' for l in m['layers']))
  for l in m['layers']:self.assertEqual(hashlib.sha256((ROOT/l['file']).read_bytes()).hexdigest(),l['sha256'])
