# GitHub Milestone Generator

A Python script for programmatically creating and closing GitHub milestones.

## (1) Setup

```shell
make install
```

## (2) Usage

```shell
python index.py --help

usage: index.py [-h] [-o {github.ibm.com,api.github.com}] -r REPOSITORY
                [-m MILESTONE_NAME] [-t MILESTONE_DUE_DATE] [-c]
                [-l {CRITICAL,ERROR,WARNING,INFO,DEBUG,TRACE}]

optional arguments:
  -h, --help            show this help message and exit
  -o {github.ibm.com,api.github.com}, --hostname {github.ibm.com,api.github.com}
                        Target GitHub API domain. Default: github.ibm.com.
  -r REPOSITORY, --repository REPOSITORY
                        Target GitHub repository.
  -m MILESTONE_NAME, --milestone-name MILESTONE_NAME
                        Create a new GitHub milestone with the specified name.
  -t MILESTONE_DUE_DATE, --milestone-due-date MILESTONE_DUE_DATE
                        Create a new GitHub milestone with the specified due date. Format: ISO 8601. e.g. 2019-07-31T23:59:59-04:00.
  -c, --close-milestones
                        Close all GitHub milestones that are overdue.
  -l {CRITICAL,ERROR,WARNING,INFO,DEBUG,TRACE}, --log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG,TRACE}
                        Target logging level. Default: INFO.

=== Environment Variables ===

GITHUB_ACCESS_TOKEN : GitHub access token.

=== Examples ===

export GITHUB_ACCESS_TOKEN=cabfe35410755fbb6c281e92902ed122144886c5

python index.py -c -o github.ibm.com -r dap/dsx-service-broker -m "MVP 3.0 - July 2019" -t 2019-07-31T23:59:59-04:00
```
