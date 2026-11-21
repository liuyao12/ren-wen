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


class PagesDeployTest(unittest.TestCase):
    def test_deploys_artifact_id_and_waits_for_success(self):
        from unittest.mock import patch
        from scripts import deploy_pages

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "output"
            env = {
                "GH_TOKEN": "github-fixture",
                "GITHUB_REPOSITORY": "liuyao12/ren-wen",
                "GITHUB_API_URL": "https://api.github.com",
                "GITHUB_RUN_ID": "123",
                "GITHUB_SHA": "a" * 40,
                "PAGES_ARTIFACT_ID": "456",
                "PAGES_ARTIFACT_NAME": "github-pages-1",
                "ACTIONS_ID_TOKEN_REQUEST_URL": "https://example.test/oidc",
                "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "oidc-fixture",
                "GITHUB_OUTPUT": str(output),
            }
            responses = [
                {"expired": False, "workflow_run": {"id": 123}, "name": "github-pages-1"},
                {"value": "oidc-value"},
                {"id": "deployment-id", "page_url": "https://liuyao12.github.io/ren-wen/"},
                {"status": "succeed"},
            ]
            with patch.dict(deploy_pages.os.environ, env), patch.object(deploy_pages.time, "sleep"):
                with patch.object(deploy_pages, "request_json", side_effect=responses) as request:
                    deploy_pages.main()
                    request.assert_any_call(
                        "https://api.github.com/repos/liuyao12/ren-wen/pages/deployments",
                        "github-fixture",
                        {"artifact_id": 456, "pages_build_version": "a" * 40, "oidc_token": "oidc-value"},
                    )
                self.assertEqual(output.read_text(), "page_url=https://liuyao12.github.io/ren-wen/\n")
                responses[0]["workflow_run"]["id"] = 999
                with patch.object(deploy_pages, "request_json", return_value=responses[0]) as request:
                    with self.assertRaises(SystemExit):
                        deploy_pages.main()
                    self.assertEqual(request.call_count, 1)
