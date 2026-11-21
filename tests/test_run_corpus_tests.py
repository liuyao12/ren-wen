import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_corpus_tests.py"


class CorpusRunnerTest(unittest.TestCase):
    def run_fixture(self, fail_on):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixture.py").write_text("EXPECTED = True\n")
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_cbr_corpus.py").write_text("""
import os
import unittest
from fixture import EXPECTED

class CorpusTests(unittest.TestCase):
    def test_worker(self):
        self.assertTrue(EXPECTED and os.environ['FIXTURE_FAIL'] != 'worker')
""")
            (tests / "test_other.py").write_text("""
import os
import unittest
from fixture import EXPECTED

class OtherTests(unittest.TestCase):
    def test_primary(self):
        self.assertTrue(EXPECTED and os.environ['FIXTURE_FAIL'] != 'primary')
""")
            return subprocess.run([sys.executable, str(SCRIPT)], cwd=root,
                                  env=dict(os.environ, FIXTURE_FAIL=fail_on),
                                  capture_output=True, text=True, timeout=15)

    def test_complete_run_and_both_exit_codes(self):
        for failure in ("", "worker", "primary"):
            with self.subTest(failure=failure):
                result = self.run_fixture(failure)
                self.assertEqual(result.returncode, bool(failure), result.stderr)
                self.assertIn("1 cases on the main process, 1 cases on the corpus worker", result.stdout)
                for name in ("test_worker (", "test_primary ("):
                    self.assertEqual(sum(line.startswith(name) for line in result.stderr.splitlines()), 1, result.stderr)
