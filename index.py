#!/usr/bin/env python3
"""
    Copyright 2019 Mike Pawlowski

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

# Pylint Rule Overrides

# Modules

import os
import re
import sys
import logging
import argparse
import datetime
import json
import github

# Authorship

# pylint: disable=unused-variable
__author__ = "Mike Pawlowski"
__copyright__ = "Copyright 2019 Mike Pawlowski"
__license__ = "Apache-2.0"
__version__ = "1.0.0"
__maintainer__ = "Mike Pawlowski"
__email__ = "TODO"
__status__ = "Production"
# pylint: enable=unused-variable

# Globals

MIN_VERSION_PYTHON = (3, 7)

# Format: ISO 8601
# UTC -04:00 (EDT)
# e.g. 2019-07-31T23:59:59-04:00
ISO_8601_DATE_REGEX = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}[+|-][0-9]{2}:[0-9]{2}$")
ISO_8601_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

GITHUB_ACCESS_TOKEN = "GITHUB_ACCESS_TOKEN"

ARGUMENT_PARSER_EPILOG = \
    "=== Environment Variables ===\n" \
    "\n" \
    "GITHUB_ACCESS_TOKEN : GitHub access token.\n" \
    "\n" \
    "=== Examples ===\n" \
    "\n" \
    "export GITHUB_ACCESS_TOKEN=cabfe35410755fbb6c281e92902ed122144886c5\n" \
    "\n" \
    "python index.py " \
    "-c " \
    "-o github.ibm.com " \
    "-r dap/dsx-service-broker " \
    "-m \"MVP 3.0 - July 2019\" " \
    "-t 2019-07-31T23:59:59-04:00 " \
    "\n"

GITHUB_ENTERPRISE_IBM_API_DOMAIN = "github.ibm.com"
GITHUB_ENTERPRISE_API_PATH = "/api/v3"
GITHUB_PUBLIC_API_DOMAIN = "api.github.com"

GITHUB_MILESTONE_STATE_OPEN = "open"
GITHUB_MILESTONE_STATE_CLOSED = "closed"

JSON_FORMAT_INDENT = 3

LOG_LEVEL_VALUE_TRACE = 5

LOG_LEVEL_NAME_CRITICAL = "CRITICAL"
LOG_LEVEL_NAME_ERROR = "ERROR"
LOG_LEVEL_NAME_WARNING = "WARNING"
LOG_LEVEL_NAME_INFO = "INFO"
LOG_LEVEL_NAME_DEBUG = "DEBUG"
LOG_LEVEL_NAME_TRACE = "TRACE"

LOGGER = logging.getLogger(__name__)

# Classes --------------------------------------------------------------------->


# Functions ------------------------------------------------------------------->

def _get_parsed_args():
    """
    Parse command-line arguments
    """

    parser = argparse.ArgumentParser(
        epilog=ARGUMENT_PARSER_EPILOG,
        formatter_class=argparse.RawTextHelpFormatter)

    # TODO: Add support for debug mode: -d

    parser.add_argument(
        "-o",
        "--hostname",
        choices=[
            GITHUB_ENTERPRISE_IBM_API_DOMAIN,
            GITHUB_PUBLIC_API_DOMAIN
        ],
        default=GITHUB_ENTERPRISE_IBM_API_DOMAIN,
        help="Target GitHub API domain. "
             "Default: {0}.".format(GITHUB_ENTERPRISE_IBM_API_DOMAIN))

    parser.add_argument(
        "-r",
        "--repository",
        required=True,
        help="Target GitHub repository.")

    parser.add_argument(
        "-m",
        "--milestone-name",
        help="Create a new GitHub milestone with the specified name.")

    parser.add_argument(
        "-t",
        "--milestone-due-date",
        help="Create a new GitHub milestone with the specified due date. "
             "Format: ISO 8601. "
             "e.g. 2019-07-31T23:59:59-04:00."
        )

    parser.add_argument(
        "-c",
        "--close-milestones",
        action="store_true",
        default=False,
        help="Close all GitHub milestones that are overdue.")

    parser.add_argument(
        "-l",
        "--log-level",
        choices=[
            LOG_LEVEL_NAME_CRITICAL,
            LOG_LEVEL_NAME_ERROR,
            LOG_LEVEL_NAME_WARNING,
            LOG_LEVEL_NAME_INFO,
            LOG_LEVEL_NAME_DEBUG,
            LOG_LEVEL_NAME_TRACE
        ],
        default=LOG_LEVEL_NAME_INFO,
        help="Target logging level. "
             "Default: {0}.".format(LOG_LEVEL_NAME_INFO))

    args = parser.parse_args()

    return args


def _init_logging_subsystem(log_level_name):
    """
    Initialize logging subsystem
    """

    # TODO: Make global / root logging level configurable (e.g. in debug mode)?
    default_log_level = logging.INFO
    log_format = "[%(asctime)s] [\033[1;31m%(levelname)-5s\033[1;0m] [%(name)s] %(message)s"
    logging.basicConfig(
        level=default_log_level,
        format=log_format)

    logging.addLevelName(LOG_LEVEL_VALUE_TRACE, LOG_LEVEL_NAME_TRACE)

    level = _get_log_level(log_level_name)

    if level is not None:
        LOGGER.setLevel(level)

    _log_trace("Logging subsystem initialized.")

    return True


def _display_parsed_args(args):
    """
    Display command-line argument values
    """

    separator = "\n"
    string_buffer = (
        "Parsed Command-line Arguments:",
        "GitHub API Domain: {0}.".format(args.hostname),
        "GitHub Repository: {0}.".format(args.repository),
        "New Milestone Name: {0}.".format(args.milestone_name),
        "New Milestone Due Date: {0}.".format(args.milestone_due_date),
        "Close Milestones: {0}.".format(args.close_milestones),
        "Logging Level: {0}.".format(args.log_level),
    )
    content = separator.join(string_buffer)

    LOGGER.info(content)


def _validate_python_version():
    """
    Validates whether the minimum Python interpreter version is satisfied.
    """

    if sys.version_info < MIN_VERSION_PYTHON:
        LOGGER.error("Python version %s.%s or later is required.", MIN_VERSION_PYTHON[0], MIN_VERSION_PYTHON[1])
        return False

    _log_trace(
        "Detected Python version: %s.%s.%s",
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro)

    return True


def _validate_env_vars():
    """
    Validate required environment variables
    """

    if not GITHUB_ACCESS_TOKEN in os.environ:
        LOGGER.error("Environment variable not defined: %s.", GITHUB_ACCESS_TOKEN)
        return False

    return True


def _validate_milestone_due_date(date):
    """
    Validate GitHub milestone due date format
    """

    status = _validate_iso_8601_date(date)

    if status:
        return True

    LOGGER.error("The specified GitHub milestone due date is not a valid ISO 8601 date: %s.", date)

    return False


def _validate_iso_8601_date(date):
    """
    Validate ISO 8601 date format
    """

    match = re.fullmatch(ISO_8601_DATE_REGEX, date)

    if match:
        return True
    return False


def _log_trace(msg, *args, **kwargs):
    """
    Log message at custom TRACE level
    """

    if _is_trace_log_level():
        LOGGER.log(LOG_LEVEL_VALUE_TRACE, msg, *args, **kwargs)


def _get_log_level(log_level_name):
    """
    Get numeric log level corresponding to specified log level name
    """

    # TODO: Is there a built-in method to do a reverse lookup?

    if log_level_name == LOG_LEVEL_NAME_CRITICAL:
        return logging.CRITICAL
    elif log_level_name == LOG_LEVEL_NAME_ERROR:
        return logging.ERROR
    elif log_level_name == LOG_LEVEL_NAME_WARNING:
        return logging.WARNING
    elif log_level_name == LOG_LEVEL_NAME_INFO:
        return logging.INFO
    elif log_level_name == LOG_LEVEL_NAME_DEBUG:
        return logging.DEBUG
    elif log_level_name == LOG_LEVEL_NAME_TRACE:
        return LOG_LEVEL_VALUE_TRACE

    return None


def _is_debug_log_level():
    """
    Determine whether the logging level is set to DEBUG or higher
    """

    if logging.DEBUG >= LOGGER.level:
        return True
    return False


def _is_trace_log_level():
    """
    Determine whether the logging level is set to TRACE or higher
    """
    if LOG_LEVEL_VALUE_TRACE >= LOGGER.level:
        return True
    return False


def _get_github_access_token():
    """
    Retrieve GitHub access token from environment variable
    """

    return os.environ[GITHUB_ACCESS_TOKEN]


def _get_github_client(hostname):
    """
    Retrieve the GitHub client
    """

    github_client = None
    github_access_token = _get_github_access_token()

    if hostname == GITHUB_ENTERPRISE_IBM_API_DOMAIN:
        # GitHub Enterprise
        github_api_url = "https://{0}{1}".format(hostname, GITHUB_ENTERPRISE_API_PATH)
    else:
        # GitHub Public
        github_api_url = "https://{0}".format(hostname)

    LOGGER.info("Connecting to GitHub API v3: %s...", github_api_url)

    try:
        github_client = github.Github(
            base_url=github_api_url,
            login_or_token=github_access_token)
    except github.GithubException as err:
        LOGGER.error("Failed to connect to GitHub API v3: %s.", github_api_url)
        _log_github_exception(err)
        return None
    except github.BadAttributeException as err:
        LOGGER.error("Failed to connect to GitHub API v3: %s.", github_api_url)
        _log_bad_attribute_exception(err)
        return None

    LOGGER.info("Successfully connected to GitHub API v3: %s.", github_api_url)

    return github_client


def _get_github_repository(github_client, repository):
    """
    Retrieve the specified GitHub repository
    """

    github_repository = None

    LOGGER.info("Retrieving GitHub repository: %s...", repository)

    try:
        github_repository = github_client.get_repo(repository)
    except github.GithubException as err:
        LOGGER.error("Failed to retrieve GitHub repository: %s.", repository)
        _log_github_exception(err)
        return None
    except github.BadAttributeException as err:
        LOGGER.error("Failed to retrieve GitHub repository: %s.", repository)
        _log_bad_attribute_exception(err)
        return None

    LOGGER.info("Successfully retrieved GitHub repository: %s.", repository)

    return github_repository


def _get_open_github_milestones(github_repository):
    """
    Retrieve all open GitHub milestones
    """

    open_milestone_count = 0
    open_milestones = None

    LOGGER.info("Retrieving all open GitHub milestones...")

    try:
        open_milestones = github_repository.get_milestones(
            state=GITHUB_MILESTONE_STATE_OPEN)
        open_milestone_count = open_milestones.totalCount
    except github.GithubException as err:
        LOGGER.error("Failed to retrieve all open GitHub milestones.")
        _log_github_exception(err)
        return None
    except github.BadAttributeException as err:
        LOGGER.error("Failed to retrieve all open GitHub milestones.")
        _log_bad_attribute_exception(err)
        return None

    LOGGER.info("Successfully retrieved all open GitHub milestones: %d.", open_milestone_count)

    is_debug_log_level = _is_debug_log_level()

    if is_debug_log_level:
        _display_github_milestones(open_milestones)

    return open_milestones


def _display_github_milestones(milestones):
    """
    Display the specified GitHub milestones
    """

    for milestone in milestones:
        _display_github_milestone(milestone)


def _display_github_milestone(milestone):
    """
    Display the specified GitHub milestone
    """

    separator = "\n"
    string_buffer = (
        "Milestone:",
        "Title: {0}.".format(milestone.title),
        "Number: {0}.".format(milestone.number),
        "State: {0}.".format(milestone.state),
        "ID: {0}.".format(milestone.id),
        "URL: {0}.".format(milestone.url),
        "Creator: {0} ({1}).".format(
            milestone.creator.login,
            milestone.creator.name),
        "Due On: {0}.".format(milestone.due_on),
        "Created At: {0}.".format(milestone.created_at),
        "Updated At: {0}.".format(milestone.updated_at),
        "Open Issues: {0}.".format(milestone.open_issues),
        "Closed Issues: {0}.".format(milestone.closed_issues),
    )
    content = separator.join(string_buffer)

    LOGGER.debug(content)


def _close_overdue_github_milestones(milestones):
    """
    Close all overdue GitHub milestones
    """

    current_time = datetime.datetime.now()
    closed_milestone_count = 0

    LOGGER.info("Closing overdue GitHub milestones (%s)...", current_time)

    for milestone in milestones:

        due_on = milestone.due_on

        if due_on and \
           isinstance(due_on, datetime.datetime) and \
           (current_time > due_on):

            status = _close_github_milestone(
                milestone=milestone)
            if status is True:
                closed_milestone_count += 1

    if closed_milestone_count == 0:
        LOGGER.info("No overdue GitHub milestones found.")
    else:
        LOGGER.info("Successfully closed overdue GitHub milestones: %d.", closed_milestone_count)


def _close_github_milestone(milestone):
    """
    Close the specified GitHub milestone
    """

    separator = "\n"
    string_buffer = (
        "Title: {0}.".format(milestone.title),
        "Number: {0}.".format(milestone.number),
        "ID: {0}.".format(milestone.id),
        "Due On: {0}.".format(milestone.due_on)
    )
    content = separator.join(string_buffer)

    LOGGER.info("Closing GitHub milestone...\n%s", content)

    try:
        milestone.edit(
            milestone.title,
            state=GITHUB_MILESTONE_STATE_CLOSED)
    except github.GithubException as err:
        LOGGER.error("Failed to close GitHub milestone.\n%s", content)
        _log_github_milestone_error(milestone)
        _log_github_exception(err)
        return False
    except github.BadAttributeException as err:
        LOGGER.error("Failed to close GitHub milestone.\n%s", content)
        _log_github_milestone_error(milestone)
        _log_bad_attribute_exception(err)
        return False

    LOGGER.info("Successfully closed GitHub milestone.\n%s", content)

    return True


def _log_github_milestone_error(milestone):
    """
    Log a GitHub milestone error
    """

    separator = "\n"
    string_buffer = (
        "Failed to close GitHub milestone:",
        "Title: {0}.".format(milestone.title),
        "Number: {0}.".format(milestone.number),
        "State: {0}.".format(milestone.state),
        "ID: {0}.".format(milestone.id),
        "URL: {0}.".format(milestone.url)
    )
    content = separator.join(string_buffer)

    LOGGER.error(content)


def _parse_date_iso_8601(iso_8601_date):
    """
    Parse the IS0 8601 date
    """
    parsed_date = None

    try:
        parsed_date = datetime.datetime.strptime(iso_8601_date, ISO_8601_DATE_FORMAT)
    except ValueError as err:
        LOGGER.error("Failed to parse ISO 8601 date: %s.", iso_8601_date)
        _log_exception(err)
        return None

    return parsed_date


def _create_milestone(github_repository, milestone_name, milestone_due_date):
    """
    Create a GitHub milestone using the specified name and due date
    """

    separator = "\n"
    string_buffer = (
        "Name: {0}.".format(milestone_name),
        "Due Date: {0}.".format(milestone_due_date)
    )
    content = separator.join(string_buffer)
    due_on = None

    LOGGER.info("Creating new GitHub milestone...\n%s", content)

    # Parse ISO 8601 date

    if milestone_due_date is not None:
        due_on = _parse_date_iso_8601(milestone_due_date)

        if due_on is None:
            LOGGER.error("Failed to create GitHub milestone.\n%s", content)
            return False

    # Create GitHub milestone

    try:
        if due_on:
            github_repository.create_milestone(
                milestone_name,
                state=GITHUB_MILESTONE_STATE_OPEN,
                due_on=due_on)
        else:
            github_repository.create_milestone(
                milestone_name,
                state=GITHUB_MILESTONE_STATE_OPEN)
    except github.GithubException as err:
        LOGGER.error("Failed to create GitHub milestone.\n%s", content)
        _log_github_exception(err)
        return False
    except github.BadAttributeException as err:
        LOGGER.error("Failed to create GitHub milestone.\n%s", content)
        _log_bad_attribute_exception(err)
        return False

    LOGGER.info("Successfully created new GitHub milestone.\n%s", content)

    return True


def _log_exception(err):
    """
    Log a general exception
    """

    separator = "\n"
    exception_name = type(err).__name__
    exception_message = str(err)
    string_buffer = (
        "Exception:",
        "Name: {0}.".format(exception_name),
        "Message: {0}.".format(exception_message)
    )
    content = separator.join(string_buffer)

    LOGGER.error(content)


def _log_github_exception(err):
    """
    Log a GitHub exception
    """

    _log_exception(err)

    separator = "\n"
    formatted_body = json.dumps(err.data, indent=JSON_FORMAT_INDENT)
    string_buffer = (
        "GitHub API Response:",
        "Status Code: {0}.".format(err.status),
        "Body: {0}.".format(formatted_body)
    )
    content = separator.join(string_buffer)

    LOGGER.error(content)


def _log_bad_attribute_exception(err):
    """
    Log a GitHub bad attribute exception
    """

    _log_exception(err)

    separator = "\n"
    string_buffer = (
        "GitHub Exception:",
        "Actual Value: {0}.".format(err.actual_value),
        "Expected Type: {0}.".format(err.expected_type),
        "Transformation Exception: {0}.".format(err.transformation_exception)
    )
    content = separator.join(string_buffer)

    LOGGER.error(content)


def _fatal_exit():
    """
    Exit script with fatal status
    """

    status = 1
    LOGGER.critical("Fatal error encountered. Exit script status: %d", status)
    sys.exit(status)


def _main():
    """
    The main function.
    """

    status = False

    # Command-line Arguments

    args = _get_parsed_args()

    # Logging

    status = _init_logging_subsystem(args.log_level)

    if status is False:
        # Should never happen
        sys.exit(1)

    # Script Banner

    LOGGER.info("[-- GitHub Milestone Generator ------------------------------------------------".upper())

    # Display command-line argument values

    _display_parsed_args(args)

    # Python Version

    status = _validate_python_version()

    if status is False:
        _fatal_exit()

    # Environment Variables

    status = _validate_env_vars()

    if status is False:
        _fatal_exit()

    # Milestone Due Date

    if args.milestone_due_date is not None:
        status = _validate_milestone_due_date(
            date=args.milestone_due_date)

        if status is False:
            _fatal_exit()

    # GitHub Client

    github_client = _get_github_client(
        hostname=args.hostname)

    if github_client is None:
        _fatal_exit()

    # GitHub Repository

    github_repository = _get_github_repository(
        github_client=github_client,
        repository=args.repository)

    if github_repository is None:
        _fatal_exit()

    # GitHub Milestones

    open_milestones = _get_open_github_milestones(
        github_repository=github_repository)

    if open_milestones is None:
        _fatal_exit()

    # Close Milestones

    if args.close_milestones and open_milestones:
        _close_overdue_github_milestones(
            milestones=open_milestones)

    # Create Milestone

    if args.milestone_name is not None:
        _create_milestone(
            github_repository=github_repository,
            milestone_name=args.milestone_name,
            milestone_due_date=args.milestone_due_date)


    sys.exit(0)


# Main ------------------------------------------------------------------------>

if __name__ == "__main__":
    _main()
