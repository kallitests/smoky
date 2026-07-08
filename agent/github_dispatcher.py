#!/usr/bin/env python3
"""
agent/github_dispatcher.py — GitHub Actions trigger + results poller

Sends a repository_dispatch event to GitHub Actions with the generated
Cypress spec file. Then polls the run until completion and downloads the
JSON results artifact.
"""

import os
import time
import base64
import logging
import requests

logger = logging.getLogger("smoky.github")

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO  = os.environ["GITHUB_REPO"]  # e.g. "kallitests/smoky"

BASE_URL = "https://api.github.com"
HEADERS  = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}


class GitHubDispatcher:

    def dispatch(
        self,
        issue_key: str,
        spec_file_name: str,
        spec_file_content: str,
        priority: str,
        environment: str,
    ) -> str:
        """
        Sends a repository_dispatch event to GitHub Actions.
        The Cypress spec file is base64-encoded in the payload so no file I/O
        is needed between the agent and the CI runner.

        Returns the run_id of the triggered workflow (by polling briefly).
        """
        encoded = base64.b64encode(spec_file_content.encode()).decode()

        payload = {
            "event_type": "smoky-trigger",
            "client_payload": {
                "issue_key": issue_key,
                "spec_file_name": spec_file_name,
                "spec_file_b64": encoded,
                "priority": priority,
                "environment": environment,
            },
        }

        url  = f"{BASE_URL}/repos/{GITHUB_REPO}/dispatches"
        resp = requests.post(url, json=payload, headers=HEADERS)

        if resp.status_code != 204:
            raise RuntimeError(
                f"GitHub dispatch failed: {resp.status_code} — {resp.text}"
            )

        logger.info(f"[github] Dispatched smoky-trigger for {issue_key}")

        # Wait briefly then find the run_id that was just created
        time.sleep(5)
        run_id = self._find_latest_run(issue_key)
        logger.info(f"[github] Run ID: {run_id}")
        return str(run_id)

    def poll_until_complete(
        self,
        run_id: str,
        timeout_seconds: int = 600,
        poll_interval: int = 15,
    ) -> dict:
        """
        Polls the GitHub Actions run every poll_interval seconds until:
          - The run completes (conclusion: success, failure, cancelled)
          - OR the timeout is reached

        Downloads and parses the smoky-results JSON artifact on completion.
        """
        url     = f"{BASE_URL}/repos/{GITHUB_REPO}/actions/runs/{run_id}"
        elapsed = 0

        while elapsed < timeout_seconds:
            resp = requests.get(url, headers=HEADERS)
            resp.raise_for_status()
            run  = resp.json()
            status     = run.get("status")
            conclusion = run.get("conclusion")

            logger.info(f"[github] Run {run_id} — status: {status} | conclusion: {conclusion}")

            if status == "completed":
                return self._download_results(run_id, conclusion)

            time.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"GitHub Actions run {run_id} timed out after {timeout_seconds}s")

    def _find_latest_run(self, issue_key: str) -> int:
        """Finds the most recent workflow run triggered by Smoky for this ticket."""
        url    = f"{BASE_URL}/repos/{GITHUB_REPO}/actions/runs"
        params = {"event": "repository_dispatch", "per_page": 5}
        resp   = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        if not runs:
            raise RuntimeError("No workflow runs found after dispatch")
        return runs[0]["id"]

    def _download_results(self, run_id: str, conclusion: str) -> dict:
        """
        Downloads the smoky-results artifact from the completed run.
        Falls back to a minimal result dict if the artifact is missing.
        """
        artifacts_url = f"{BASE_URL}/repos/{GITHUB_REPO}/actions/runs/{run_id}/artifacts"
        resp = requests.get(artifacts_url, headers=HEADERS)
        resp.raise_for_status()

        artifacts = resp.json().get("artifacts", [])
        results_artifact = next(
            (a for a in artifacts if a["name"] == "smoky-results"), None
        )

        if not results_artifact:
            logger.warning(f"[github] No smoky-results artifact found for run {run_id}")
            return {
                "run_id": run_id,
                "conclusion": conclusion,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration_ms": 0,
                "scenarios": [],
                "error": "No results artifact found",
            }

        # Download the artifact zip
        download_url = results_artifact["archive_download_url"]
        dl_resp = requests.get(download_url, headers=HEADERS, allow_redirects=True)
        dl_resp.raise_for_status()

        # Extract the JSON from the zip in memory
        import zipfile
        import io
        import json

        with zipfile.ZipFile(io.BytesIO(dl_resp.content)) as z:
            json_files = [f for f in z.namelist() if f.endswith(".json")]
            if not json_files:
                return {"run_id": run_id, "conclusion": conclusion, "error": "Empty artifact"}
            with z.open(json_files[0]) as f:
                results = json.load(f)

        results["run_id"] = run_id
        results["conclusion"] = conclusion
        return results
