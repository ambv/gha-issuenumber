# gha-issuenumber
A GitHub action that enforces all commits have issue numbers linked.
It supports silencing the check via a "skip issue" label on a given
pull request.  To support this, it's configured as two workflows:

## 1. The check

```yaml
name: Issue Number

on:
  push:
    branches:
      - master
      - ci
  pull_request:
    branches:
      - '*'

jobs:
  issuenumber-job:
    runs-on: ubuntu-latest
    name: Check Commit Messages

    steps:
    - uses: actions/checkout@v1
      with:
        fetch-depth: 10
        submodules: false
    - uses: ambv/gha-issuenumber/check@master
      id: issuenumber
    - name: Check output
      run: "echo \"Last issue number is ${{ steps.issuenumber.outputs.issuenumber }}\""
```

## 2. A trigger to re-run the check on label changes

GitHub Actions have a limitation/bug that causes checks triggered by
"labeled" and "unlabeled" types of events on pull requests to be
duplicated on the pull request body.  In other words, if the check
for issue numbers failed initially, and you added the "skip issue" label
later, GitHub would create a *new* run of the check and list it
**next to** the old one.  You'd have one failing check and one
successful check.  This makes it impossible to approve a pull request if
you're enforcing that checks must pass before merging.

To work around this, we introduce a trigger for those event types that
simply hits "Re-run" on a pre-existing check.

```yaml
name: Re-Run

on:
  pull_request:
    types: [labeled, unlabeled]
    branches:
      - '*'

jobs:
  issuenumber-job:
    runs-on: ubuntu-latest
    name: Issue Number

    steps:
    - uses: ambv/gha-issuenumber/trigger@master
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        check_to_rerun: "Check Commit Messages"
```