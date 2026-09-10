"""Synthetic mutations test validation; they are never written to the corpus."""
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from scripts.profiles import canonical_name, sui_age, validate_profile, load_profiles, index_db

ROOT = Path(__file__).resolve().parents[1]

class ProfilesTest(unittest.TestCase):
    def setUp(self):
        self.profile = copy.deepcopy(load_profiles(ROOT)[0])

    def test_name(self):
        self.assertEqual(canonical_name(self.profile), '[湘鄉] 曾紀澤')

    def test_sui(self):
        self.assertEqual(sui_age(1839, 1890), 52)
        self.assertEqual(sui_age(1839, 1839), 1)
        self.assertEqual(sui_age(1839, 1840), 2)

    def test_unknown_and_invalid_ages(self):
        for birth, event in [(None, 1890), (1839, None), (True, 2), (1840, 1839), ('1839', 1890), (0, 1)]:
            self.assertIsNone(sui_age(birth, event))

    def test_lunar_year_boundary_not_gregorian_year(self):
        self.assertEqual(sui_age(1890, 1899), 10)
        p = self.profile
        p['life']['birth']['chineseYear'] = 1890
        p['life']['death']['chineseYear'] = 1899
        p['life']['westernDates'] = [{'event':'death','calendar':'gregorian','value':'1900-01-01','source':'eccp'}]
        validate_profile(p)
        self.assertEqual(sui_age(p['life']['birth']['chineseYear'], p['life']['death']['chineseYear']), 10)

    def test_unknown_chinese_year_not_inferred_from_western_date(self):
        self.profile['life']['birth'] = None
        validate_profile(self.profile)
        self.assertIsNone(sui_age(None, 1890))

    def test_hao_is_not_zi(self):
        p = self.profile
        p['name']['hao'] = [{'value': '測試號', 'source': 'eccp'}]
        p['name']['parenthetical'] = {'kind': 'hao', 'value': '測試號'}
        validate_profile(p)
        self.assertEqual(canonical_name(p), '[湘鄉] 曾紀澤')
        self.assertEqual(p['name']['hao'][0]['value'], '測試號')
        self.assertNotIn('（', canonical_name(p))
        p['name']['parenthetical']['kind'] = 'zi'
        with self.assertRaises(ValueError): validate_profile(p)

    def test_unknown_native_place_and_alias_omitted(self):
        self.profile['name']['jiguan'] = None
        self.profile['name']['bracket'] = None
        self.profile['name']['parenthetical'] = None
        self.assertEqual(canonical_name(self.profile), '曾紀澤')
        validate_profile(self.profile)

    def test_external_ids_are_strings(self):
        self.assertEqual(self.profile['externalIds']['geni']['id'], '6000000012827521360')
        for provider in ['geni', 'cbdb']:
            p = copy.deepcopy(self.profile)
            p['externalIds'][provider]['id'] = int(p['externalIds'][provider]['id'])
            with self.assertRaises(ValueError): validate_profile(p)

    def test_unresolved_external_slot(self):
        self.profile['externalIds']['geni'] = {'id': None, 'status': 'not-searched'}
        validate_profile(self.profile)
        self.profile['externalIds']['geni']['status'] = 'matched'
        with self.assertRaises(ValueError): validate_profile(self.profile)

    def test_source_required(self):
        self.profile['life']['birth']['source'] = 'invented'
        with self.assertRaises(ValueError): validate_profile(self.profile)

    def test_no_false_review(self):
        self.profile['reviewStatus'] = 'reviewed'
        with self.assertRaises(ValueError): validate_profile(self.profile)

    def test_invalid_year(self):
        self.profile['life']['death']['chineseYear'] = 1800
        with self.assertRaises(ValueError): validate_profile(self.profile)

    def test_invalid_exact_date(self):
        self.profile['life']['westernDates'][0]['value'] = '1839-02-30'
        with self.assertRaises(ValueError): validate_profile(self.profile)

    def test_sql_index_is_derived_and_keeps_ids_as_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'renwen.sqlite'
            db = sqlite3.connect(path)
            db.execute('CREATE TABLE entities(id TEXT PRIMARY KEY, type TEXT)')
            db.execute('INSERT INTO entities VALUES(?,?)', ('person-zeng-jize','person'))
            db.commit(); db.close()
            index_db(path, ROOT)
            index_db(path, ROOT)
            db = sqlite3.connect(path)
            self.assertEqual(db.execute("SELECT canonical_name,sui_at_death FROM person_profile_summary WHERE id='person-zeng-jize'").fetchone(), ('[湘鄉] 曾紀澤',52))
            self.assertEqual(db.execute("SELECT external_id,typeof(external_id) FROM person_external_ids WHERE provider='geni' AND person_id='person-zeng-jize'").fetchone(), ('6000000012827521360','text'))
            db.close()

    def test_index_refuses_missing_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): index_db(Path(tmp)/'missing.sqlite', ROOT)

if __name__ == '__main__':
    unittest.main()
