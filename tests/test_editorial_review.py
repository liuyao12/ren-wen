import json,unittest
from pathlib import Path
from scripts.renwen import TextIndex
ROOT=Path(__file__).resolve().parents[1]
class EditorialReview(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=json.loads((ROOT/'data/catalog.json').read_text());cls.q=json.loads((ROOT/'data/editorial/identification-review.json').read_text());cls.ms={m['id']:m for m in cls.c['mentions']};cls.sources={s['id']:s for s in cls.c['sources']}
 def test_quarantined_ids_remain_in_text_but_not_as_identifications(self):
  texts={}
  for m in self.q['quarantined']:
   if m['witness'] not in texts:texts[m['witness']]=TextIndex((ROOT/self.sources[m['witness']]['text']).read_text())
   doc=texts[m['witness']];self.assertIn(m['id'],doc.ids);self.assertNotIn(m['id'],doc.mentions);self.assertNotIn(m['id'],self.ms)
 def test_akedun_chronology_is_not_zengs(self):
  m=self.ms['eccp-3633207-003-n011'];self.assertEqual(m['entity'],'work-akedun-nianpu');self.assertEqual(m['quote'],"nien-p'u")
 def test_emperors_are_contextual_not_date_terms(self):
  expected={'eccp-3633207-001':'person-eccp-3678153','eccp-3633207-002':'person-hongli'}
  for p,e in expected.items():
   ms=[m for m in self.ms.values() if m['passage']==p and m['quote']=='the emperor'];self.assertEqual([m['entity'] for m in ms],[e])
  qsg=[m for m in self.ms.values() if m['passage']=='qsg-volume-303-026' and m['quote']=='上'];self.assertEqual(len(qsg),4);self.assertTrue(all(m['entity']=='person-hongli' for m in qsg))
 def test_no_typographic_guess_is_promoted_to_reviewed(self):
  self.assertTrue(all(m['status']=='needs-review' for m in self.q['quarantined']));self.assertTrue(all(d['after']['status']=='proposed' for d in self.q['decisions']))
 def test_every_work_has_active_or_quarantined_evidence(self):
  index=json.loads((ROOT/'data/works/index.json').read_text())
  for name in index['works']:
   p=json.loads((ROOT/'data/works'/name).read_text());self.assertTrue(p['mentions'] or p.get('quarantinedMentions'))
 def test_archived_redirect_inventory_is_preserved(self):
  self.assertEqual(sum(s.get('kind')=='cross-reference' for s in self.c['sources']),193);self.assertGreater(len(self.c['navigation']['redirects']),180)
