"""Run the complete CBR unittest suite with one worker for expensive corpus cases."""

from pathlib import Path
import subprocess
import sys
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
    with subprocess.Popen(command) as child:
        primary_passed = runner.run(primary).wasSuccessful()
        worker_status = child.wait()
    return int(not primary_passed or worker_status != 0)


if __name__ == "__main__":
    raise SystemExit(main())
