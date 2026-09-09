"""Synthetic edits exercise mechanics; they are not proposed historical corrections."""
import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import shutil

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('renwen',ROOT/'scripts/renwen.py')
rw=importlib.util.module_from_spec(spec);spec.loader.exec_module(rw)

class CorpusTests(unittest.TestCase):
    def setUp(self): self.c=rw.load_catalog()
    def proposal(self):
        m=self.c['mentions'][0];s=self.c['sources'][0]
        return dict(schemaVersion=1,id='test-proposal',operation='relink-mention',witness=s['id'],mention=m['id'],baseSha256=s['sha256'],before=m['entity'],after='person-zeng-guofan',reason='Synthetic test of review mechanics; not a historical judgment.',status='proposed')
    def test_corpus_valid(self): self.assertEqual(rw.validate()['mentions'],len(self.c['mentions']))
    def test_all_sources_declare_extent(self): self.assertTrue(all(s['extent'] for s in self.c['sources']))
    def test_no_fabricated_jurisdictions(self): self.assertEqual(self.c['jurisdictions'],[])
    def test_unknown_lives_not_estimated(self): self.assertIsNone(next(e for e in self.c['entities'] if e['id']=='person-macartney')['life'])
    def test_cross_reference_not_identity(self):
        c=rw.context('eccp-03'); mac=[m for m in c['mentions'] if 'Macartney' in m['quote']]
        self.assertEqual(mac[0]['entity'],'person-macartney')
    def test_context_preserves_original_date(self):
        c=rw.context('qsg-01');self.assertEqual(c['events'][0]['time']['original'],'光緒四年')
    def test_rejects_unknown_context(self):
        with self.assertRaises(ValueError): rw.context('missing')
    def test_rejects_escaping_path(self):
        with self.assertRaises(ValueError): rw.inside(ROOT,'../secret')
    def test_rejects_duplicate_anchor(self):
        with self.assertRaises(ValueError):rw.TextIndex('<p id="a">甲</p><p id="a">乙</p>')
    def test_rejects_executable_html(self):
        for text in ['<p id="a"><script>alert(1)</script></p>','<p id="a" onclick="x">text</p>','<p id="a"><a href="javascript:alert(1)">x</a></p>']:
            with self.assertRaises(ValueError):rw.TextIndex(text)
    def test_valid_proposal(self): self.assertEqual(rw.validate_proposal(self.proposal(),self.c)['id'],'test-proposal')
    def test_stale_proposal(self):
        p=self.proposal();p['baseSha256']='0'*64
        with self.assertRaises(ValueError):rw.validate_proposal(p,self.c)
    def test_wrong_original(self):
        p=self.proposal();p['before']='person-guo-songtao'
        with self.assertRaises(ValueError):rw.validate_proposal(p,self.c)
    def test_unknown_target(self):
        p=self.proposal();p['after']='person-invented'
        with self.assertRaises(ValueError):rw.validate_proposal(p,self.c)
    def test_accepted_proposal_cannot_reenter(self):
        p=self.proposal();p['status']='accepted'
        with self.assertRaises(ValueError):rw.validate_proposal(p,self.c)
    def test_punctuation_is_not_harmless(self):
        result=rw.collate('甲，乙。','甲乙。');self.assertEqual(result['kind'],'punctuation-or-whitespace');self.assertTrue(result['requiresInterpretationReview'])
    def test_wording_variant(self): self.assertEqual(rw.collate('五年授官。','六年授官。')['kind'],'wording')
    def test_unchanged_collation(self): self.assertEqual(rw.collate('甲。','甲。')['kind'],'unchanged')
    def test_markup_not_wording(self):
        a='<p id="a">甲。</p>';b='<p id="a"><span id="m" data-entity="p">甲</span>。</p>'
        self.assertEqual(rw.collate(a,b)['kind'],'unchanged')
    def test_xml_preserves_unknown_fields(self):
        raw=b'<?xml version="1.0"?><synthetic custom="yes"><span future="unknown">text</span></synthetic>\n'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.xml';p.write_bytes(raw)
            result=rw.stage_xml(p,Path(d)/'out','https://example.org/test','Synthetic test data')
            self.assertEqual((Path(d)/'out/input.xml').read_bytes(),raw);self.assertEqual(result['semanticCompatibility'],'unverified')
    def test_xml_entities_rejected(self):
        for raw in [b'<!DOCTYPE r [<!ENTITY e "x">]><r>&e;</r>',b'<!ENTITY e SYSTEM "file:///etc/passwd"><r/>']:
            with self.assertRaises(ValueError): rw.inspect_xml(raw)
    def test_checksum_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);shutil.copytree(ROOT/'data',root/'data')
            with (root/'data/texts/eccp.html').open('a') as f:f.write('x')
            with self.assertRaises(ValueError):rw.validate(root)
    def test_build_sqlite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'db.sqlite';rw.build_db(p)
            with sqlite3.connect(p) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM mentions').fetchone()[0],len(self.c['mentions']))
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
    def test_apply_is_explicit_and_keeps_upstream(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);shutil.copytree(ROOT/'data',root/'data');p=root/'proposals.json';p.write_text(json.dumps([self.proposal()]))
            old=(root/'data/upstream/eccp.html').read_bytes();result=rw.apply_proposals(p,'Unit test only',root)
            self.assertEqual(result['accepted'],1);self.assertEqual((root/'data/upstream/eccp.html').read_bytes(),old)
            self.assertTrue((root/'data/reviews.jsonl').exists());rw.validate(root)
    def test_merge_never_overwrites_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            base,ours,theirs=[Path(d)/s for s in ['base','ours','theirs']]
            base.write_text('first\nsecond\nthird\n');ours.write_text('FIRST\nsecond\nthird\n');theirs.write_text('first\nsecond\nTHIRD\n')
            result=rw.merge_candidate(base,ours,theirs,Path(d)/'candidate')
            self.assertEqual(result['conflicts'],0);self.assertFalse(result['applied']);self.assertEqual(base.read_text(),'first\nsecond\nthird\n')
            with self.assertRaises(ValueError):rw.merge_candidate(base,ours,theirs,base)

if __name__=='__main__': unittest.main()
