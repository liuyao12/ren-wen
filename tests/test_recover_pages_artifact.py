import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts.recover_pages_artifact import VERIFICATION_STEPS, verify_archive, verify_run


class PagesRecoveryTest(unittest.TestCase):
    repository = "liuyao12/ren-wen"
    revision = "1" * 40
    verified_run = {
        "id": 123,
        "head_sha": "2" * 40,
        "status": "completed",
        "event": "workflow_dispatch",
        "head_branch": "main",
        "head_repository": {"full_name": repository},
        "path": ".github/workflows/pages.yml",
    }

    def test_main_run_requires_both_verifications(self):
        steps = [{"name": name, "conclusion": "success"} for name in VERIFICATION_STEPS]
        verify_run(self.verified_run, [{"name": "deploy", "steps": steps}], self.repository)
        with self.assertRaises(SystemExit):
            verify_run(self.verified_run, [{"name": "deploy", "steps": steps[:1]}], self.repository)
        with self.assertRaises(SystemExit):
            verify_run(dict(self.verified_run, head_branch="other"), [{"name": "deploy", "steps": steps}], self.repository)

    def test_archive_binds_the_source_and_workflow(self):
        stamp = {
            "commit": self.revision,
            "sourceRepository": "liuyao12/chinese-biographical-repository",
            "deploymentRepository": self.repository,
            "deploymentRunId": "123",
            "deploymentWorkflowCommit": self.verified_run["head_sha"],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.tar"
            data = json.dumps(stamp).encode()
            entry = tarfile.TarInfo("./deployment.json")
            entry.size = len(data)
            with tarfile.open(path, "w") as archive:
                archive.addfile(entry, io.BytesIO(data))
            verify_archive(path, self.revision, self.verified_run, self.repository)
            with self.assertRaises(SystemExit):
                verify_archive(path, "3" * 40, self.verified_run, self.repository)
            with self.assertRaises(SystemExit):
                verify_archive(path, self.revision, dict(self.verified_run, id=124), self.repository)
