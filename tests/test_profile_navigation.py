"""Reference profiles and year-only claims, without asserting independent human review."""
import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path
from scripts.profiles import load_profiles, validate_profile, index_db
ROOT = Path(__file__).resolve().parents[1]

class ProfileNavigationTest(unittest.TestCase):
    def test_year_only_claim_validated(self):
        p = copy.deepcopy(load_profiles(ROOT)[0])
        p['life']['westernYears'] = [{'event':'birth','calendar':'gregorian','value':1839,'source':'eccp'}]
        validate_profile(p)
        p['life']['westernYears'][0]['value'] = True
        with self.assertRaises(ValueError): validate_profile(p)
        p['life']['westernYears'][0]['value'] = 1839
        p['life']['westernYears'][0]['source'] = 'missing'
        with self.assertRaises(ValueError): validate_profile(p)

    def test_profile_without_annotated_mention_is_indexed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.sqlite'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE entities(id TEXT PRIMARY KEY,type TEXT,label TEXT,metadata TEXT)')
            index_db(path,ROOT)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("SELECT type,label FROM entities WHERE id='person-dong-xun'").fetchone(),('person','董恂'))
                self.assertEqual(db.execute('SELECT COUNT(*) FROM person_profiles').fetchone()[0],len(load_profiles(ROOT)))

    def test_profile_cannot_overwrite_a_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.sqlite'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE entities(id TEXT PRIMARY KEY,type TEXT,label TEXT,metadata TEXT)')
                db.execute("INSERT INTO entities VALUES('person-zeng-jize','place','unrelated','{}')")
            with self.assertRaises(ValueError): index_db(path,ROOT)

    def test_reference_profiles_keep_unknown_identifiers(self):
        people={p['id']:p for p in load_profiles(ROOT)}
        for key in ['person-guo-songtao','person-macartney','person-chonghou','person-dong-xun']:
            for x in people[key]['externalIds'].values():
                self.assertIsNone(x['id'])
                self.assertEqual(x['status'],'not-searched')
        zeng=people['person-zeng-guofan']['externalIds']
        self.assertEqual(zeng['cbdb']['id'],'34344')
        self.assertTrue(zeng['cbdb']['evidence'])
        self.assertIsNone(zeng['geni']['id'])
        self.assertEqual(zeng['geni']['status'],'unresolved')
        self.assertIsNone(people['person-macartney']['life']['birth'])
        self.assertIsNone(people['person-chonghou']['name']['jiguan'])
