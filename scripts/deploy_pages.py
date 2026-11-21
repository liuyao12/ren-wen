"""Deploy a verified artifact by ID through the GitHub Pages REST API."""

import json
import os
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request_json(url, token, payload=None):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    with urlopen(Request(url, data=data, headers=headers), timeout=30) as response:
        return json.load(response)


def main():
    github_token = os.environ["GH_TOKEN"]
    repository = os.environ["GITHUB_REPOSITORY"]
    api = f"{os.environ['GITHUB_API_URL']}/repos/{repository}"
    run_id = int(os.environ["GITHUB_RUN_ID"])
    sha = os.environ["GITHUB_SHA"]
    artifact_id = int(os.environ["PAGES_ARTIFACT_ID"])

    for attempt in range(24):
        try:
            artifact = request_json(f"{api}/actions/artifacts/{artifact_id}", github_token)
        except HTTPError as error:
            if error.code != 404 or attempt == 23:
                raise
            time.sleep(5)
        else:
            break
    if (artifact["expired"] or artifact["workflow_run"]["id"] != run_id
            or artifact["name"] != os.environ["PAGES_ARTIFACT_NAME"]):
        raise SystemExit("The Pages artifact does not match this workflow attempt.")

    oidc = request_json(
        os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"], os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
    )["value"]
    deployment = request_json(f"{api}/pages/deployments", github_token, {
        "artifact_id": artifact_id,
        "pages_build_version": sha,
        "oidc_token": oidc,
    })
    deployment_id = deployment.get("id") or deployment["status_url"].rsplit("/", 1)[-1]
    endpoint = f"{api}/pages/deployments/{deployment_id}"
    print(f"Deploying Pages artifact {artifact_id} as deployment {deployment_id}.", flush=True)
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        time.sleep(5)
        try:
            status = request_json(endpoint, github_token)["status"]
        except HTTPError as error:
            if error.code not in {404, 429, 500, 502, 503, 504}:
                raise
            continue
        if status == "succeed":
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                print(f"page_url={deployment['page_url']}", file=output)
            return
        if status in {"deployment_failed", "deployment_perms_error", "deployment_content_failed",
                      "deployment_cancelled", "deployment_lost"}:
            raise SystemExit(f"GitHub Pages deployment failed: {status}")
    raise SystemExit(f"GitHub Pages deployment {deployment_id} timed out.")


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        raise SystemExit(f"GitHub returned HTTP {error.code} (request {error.headers.get('X-GitHub-Request-Id', 'unknown')}).")
