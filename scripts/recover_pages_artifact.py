"""Reuse the staged site from a completed, verified main Pages run."""

import json
import os
import re
import subprocess
import tarfile
from pathlib import Path


VERIFICATION_STEPS = {
    "Validate the complete corpus and dated-name records",
    "Test the exact staged site before deployment",
}


def gh_json(path):
    return json.loads(subprocess.check_output(["gh", "api", path]))


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def verify_run(run, jobs, repository):
    require(
        run.get("status") == "completed"
        and run.get("event") in {"push", "workflow_dispatch"}
        and run.get("head_branch") == "main"
        and (run.get("head_repository") or {}).get("full_name") == repository
        and run.get("path") == ".github/workflows/pages.yml",
        "Recovery requires a completed Pages run from this repository's main branch.",
    )
    require(
        any(
            job.get("name") == "deploy"
            and VERIFICATION_STEPS <= {
                step["name"] for step in job.get("steps", []) if step.get("conclusion") == "success"
            }
            for job in jobs
        ),
        "The previous run did not pass corpus and staged site verification.",
    )


def verify_archive(path, commit, run, repository):
    with tarfile.open(path, "r:*") as archive:
        stamps = [p for p in archive if p.name.removeprefix("./") == "deployment.json"]
        require(len(stamps) == 1 and stamps[0].isfile() and stamps[0].size < 1_000_000,
                "The staged site must contain one regular deployment manifest.")
        stamp = json.load(archive.extractfile(stamps[0]))
    require(
        stamp.get("commit") == commit
        and stamp.get("sourceRepository") == "liuyao12/chinese-biographical-repository"
        and stamp.get("deploymentRepository") == repository
        and stamp.get("deploymentRunId") == str(run["id"])
        and stamp.get("deploymentWorkflowCommit") == run["head_sha"],
        "The artifact manifest does not match the exact CBR commit and verified workflow run.",
    )


def main():
    repository = os.environ["GITHUB_REPOSITORY"]
    previous_id = os.environ["VALIDATED_RUN_ID"]
    commit = os.environ["EXPECTED_COMMIT"]
    require(re.fullmatch(r"[1-9][0-9]*", previous_id), "Expected a numeric previous run ID.")
    require(os.environ["REQUESTED_SOURCE"] == commit and re.fullmatch(r"[0-9a-f]{40}", commit),
            "Recovery requires an exact CBR commit in source_ref.")

    endpoint = f"repos/{repository}/actions/runs/{previous_id}"
    run = gh_json(endpoint)
    require(str(run["id"]) == previous_id, "Unexpected Pages run in the API response.")
    attempt = run["run_attempt"]
    jobs = gh_json(f"{endpoint}/attempts/{attempt}/jobs")["jobs"]
    verify_run(run, jobs, repository)
    artifacts = gh_json(f"{endpoint}/artifacts")["artifacts"]
    name = f"github-pages-{attempt}"
    matches = [a for a in artifacts if a["name"] == name and not a["expired"]]
    if not matches and attempt == 1:
        name = "github-pages"
        matches = [a for a in artifacts if a["name"] == name and not a["expired"]]
    require(len(matches) == 1, "Expected exactly one unexpired verified Pages artifact.")

    folder = Path(os.environ["RUNNER_TEMP"]) / "verified-pages"
    subprocess.run(
        ["gh", "run", "download", previous_id, "--repo", repository, "--name", name, "--dir", str(folder)],
        check=True,
    )
    verify_archive(folder / "artifact.tar", commit, run, repository)
    print(f"Verified Pages artifact {matches[0]['id']} from run {previous_id} for {commit}.")


if __name__ == "__main__":
    main()
