#!/usr/bin/env python3.8
from __future__ import annotations
from typing import *  # NoQA

import contextlib
import json
import os
import re
import sys


ISSUE_NUMBER_RE = re.compile(r"#(?P<issuenumber>\d+)")


def read_event_json():
    with open("/github/workflow/event.json") as jf:
        return json.load(jf)


def ensure_issue_numbers_in_event(event: Dict[str, Any]) -> int:
    last_issue_number = 0
    if "pull_request" in event:
        for commit_id, issue_numbers in gen_issue_numbers_from_git(
            commit_count=event["pull_request"]["commits"],
            base_sha=event["pull_request"]["base"]["sha"],
            head_sha=event["pull_request"]["head"]["sha"],
        ):
            if not issue_numbers:
                raise LookupError(commit_id)
            last_issue_number = issue_numbers[0]
        return last_issue_number

    for commit in event["commits"]:
        if m := ISSUE_NUMBER_RE.search(commit["message"]):
            last_issue_number = int(m.group("issuenumber"))
        else:
            raise LookupError(commit["id"])
    return last_issue_number


def gen_issue_numbers_from_git(
    *, commit_count: int, base_sha: str, head_sha: str,
) -> Iterator[Tuple[str, List[int]]]:
    from dulwich import repo

    r = repo.Repo(".")
    walker = r.get_walker(max_entries=commit_count + 2, reverse=True)
    for entry in walker:
        sha = entry.commit.id.decode("utf8")
        message = entry.commit.message.decode("utf8")
        issue_numbers = [int(num) for num in ISSUE_NUMBER_RE.findall(message)]

        if base_sha:
            if base_sha == sha:
                base_sha = ""
            continue

        print(
            f"Checked {sha}: {len(issue_numbers)} issue numbers",
            file=sys.stderr,
        )
        print(message, end="\n\n")
        yield (sha, issue_numbers)
        if sha == head_sha:
            break


def is_pull_request_with_skip_issue_label(event: Dict[str, Any]) -> bool:
    with contextlib.suppress(KeyError):
        for label in event["pull_request"]["labels"]:
            if label["name"].lower() == "skip issue":
                return True

    return False


last_issue_number: Union[int, str]
event = read_event_json()
try:
    if is_pull_request_with_skip_issue_label(event):
        last_issue_number = "skipped by label"
    else:
        last_issue_number = ensure_issue_numbers_in_event(event)
except LookupError as le:
    print(
        f"No issue number given in the commit message for commit {le}",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"::set-output name=issuenumber::{last_issue_number}")
