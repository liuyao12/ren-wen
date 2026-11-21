"""Run the complete CBR unittest suite with one worker for expensive corpus cases."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


def iter_cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_cases(item)
        else:
            yield item


def split_corpus_cases(suite):
    cases = list(iter_cases(suite))
    hot = [index for index, case in enumerate(cases)
           if case.id().startswith("test_cbr_corpus.CorpusTests.")]
    # Release logs put this class at about four fifths of the total runtime.
    # Moving five eighths of it balances the worker against all remaining tests.
    worker = {index for slot, index in enumerate(hot) if slot % 8 < 5}
    return (
        unittest.TestSuite(case for index, case in enumerate(cases) if index not in worker),
        [cases[index].id() for index in sorted(worker)],
    )


def main():
    sys.path.insert(0, str(Path.cwd()))
    runner = unittest.TextTestRunner(verbosity=2)
    if sys.argv[1:2] == ["--worker"]:
        sys.path.insert(0, str(Path("tests").resolve()))
        suite = unittest.TestLoader().loadTestsFromNames(sys.argv[2:])
        return int(not runner.run(suite).wasSuccessful())

    primary, worker = split_corpus_cases(unittest.TestLoader().discover("tests"))
    print(f"CBR unittest: {primary.countTestCases()} cases on the main process, "
          f"{len(worker)} cases on the corpus worker.", flush=True)
    if not worker:
        return int(not runner.run(primary).wasSuccessful())

    command = [sys.executable, str(Path(__file__).resolve()), "--worker", *worker]
    # unittest writes case names and outcomes separately. Keep the two streams
    # apart so an interleaved "FAIL" cannot be attributed to the wrong case.
    worker_env = dict(os.environ, PYTHONIOENCODING="utf-8")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log, subprocess.Popen(
        command, stdout=log, stderr=subprocess.STDOUT, env=worker_env
    ) as child:
        primary_passed = runner.run(primary).wasSuccessful()
        worker_status = child.wait()
        log.seek(0)
        print("CBR corpus worker results:", file=sys.stderr)
        shutil.copyfileobj(log, sys.stderr)
    return int(not primary_passed or worker_status != 0)


if __name__ == "__main__":
    raise SystemExit(main())
