#!/usr/bin/env python3.8
from __future__ import annotations
from typing import *  # NoQA

import json
import operator
import os
import sys

import httpx


API = "https://api.github.com"


def read_event_json() -> Dict[str, Any]:
    with open("/github/workflow/event.json") as jf:
        return json.load(jf)


def get_previous_run(
    org: str, repo: str, pr_commit: str, check_name: str, github_token: str
) -> Dict[str, Any]:
    response = httpx.get(
        f"{API}/repos/{org}/{repo}/commits/{pr_commit}/check-runs",
        headers=[
            ("authorization", f"token {github_token}"),
            ("accept", "application/vnd.github.v3+json"),
            ("accept", "application/vnd.github.antiope-preview+json"),
        ],
    )
    runs = response.json()['check_runs']
    runs = [run for run in runs if run['name'] == check_name]

    if not runs:
        raise LookupError(check_name)

    runs.sort(key=operator.itemgetter("started_at"))
    return runs[-1]


def rerequest(org: str, repo: str, suite_id: str, github_token: str) -> None:
    url = f"{API}/repos/{org}/{repo}/check-suites/{suite_id}/rerequest"
    print("Re-requesting {url}...", file=sys.stderr)
    response = httpx.post(
        url,
        headers=[
            ("authorization", f"token {github_token}"),
            ("accept", "application/vnd.github.v3+json"),
            ("accept", "application/vnd.github.antiope-preview+json"),
        ],
    )
    print(response.status_code, file=sys.stderr)


def main() -> None:
    event = read_event_json()
    org = event['pull_request']['base']['repo']['owner']['login']
    repo = event['pull_request']['base']['repo']['name']
    pr_commit = event['pull_request']['head']['sha']
    token = os.environ['INPUT_GITHUB_TOKEN']
    check = os.environ['INPUT_CHECK_TO_RERUN']
    try:
        previous_run = get_previous_run(org, repo, pr_commit, check, token)
    except LookupError:
        print(f"No previous run of {check} found", file=sys.stderr)
        return

    rerequest(org, repo, previous_run["check_suite"]["id"], token)


if __name__ == "__main__":
    main()