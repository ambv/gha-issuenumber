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
        commit_count = event["pull_request"]["commits"]
        for commit_id, issue_numbers in gen_issue_numbers_from_git(
            commit_count=commit_count
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
    *, commit_count: int
) -> Iterator[Tuple[str, List[int]]]:
    from dulwich import repo

    r = repo.Repo(".")
    walker = r.get_walker(max_entries=commit_count, reverse=True)
    for entry in walker:
        sha = entry.commit.id.decode("utf8")
        message = entry.commit.message.decode("utf8")
        if issue_numbers := ISSUE_NUMBER_RE.findall(message):
            issue_numbers_int = [int(num) for num in issue_numbers]
            yield (sha, issue_numbers_int)


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
