import unittest,json,tempfile,shutil
from pathlib import Path
from scripts.name_history import validate,ROOT
class NameHistoryTests(unittest.TestCase):
    def test_published_name_periods_have_exact_evidence(self):
        result=validate();self.assertTrue(result['valid']);self.assertGreater(result['periods'],0)
    def test_personal_names_have_a_different_clock_from_source_dates(self):
        d=json.loads((ROOT/'data/name-history.json').read_text());self.assertEqual(d['workDates']['work-eccp']['kind'],'edition-imprint');self.assertIsNone(d['people']['person-zeng-guofan']['names'][0]['from'])
