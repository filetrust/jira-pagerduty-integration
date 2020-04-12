import json
import logging
import os

from jira import JIRA
from jira.exceptions import JIRAError
from pdpyras import APISession

from jpi import settings


jira = None
pagerduty = None
questions = None
logger = logging.getLogger()
severity_field_id = None


def get_jira():
    global jira
    if jira is None:
        options = {"server": os.environ["JIRA_SERVER_URL"]}
        basic_auth = (
            os.environ["JIRA_USER_EMAIL"],
            os.environ["JIRA_API_TOKEN"],
        )
        jira = JIRA(options, basic_auth=basic_auth)
    return jira


def get_pagerduty():
    global pagerduty
    if pagerduty is None:
        api_token = os.environ["PAGERDUTY_API_TOKEN"]
        user_email_from = os.environ["PAGERDUTY_USER_EMAIL"]
        pagerduty = APISession(api_token, default_from=user_email_from)
    return pagerduty


def get_questions():
    global questions
    if questions is None:
        questions_file = os.path.join(
            settings.PROJECT_PATH, os.environ["QUESTIONS_FILE"]
        )
        try:
            with open(questions_file, "r") as f:
                questions = json.loads(f.read())
        except Exception:
            questions = []
            logger.exception(
                f"Error occurred while reading the predefined "
                f"questions from the file: {questions_file}"
            )
    return questions


def link_issue(outward, inward, link_type):
    """
    Create a link between two issues. `inward` is an issue to link
    from, `outward` is an issue to link to and `link_type` is the type
    of link to create. `inward` and `outward` are the keys of the
    issues that are being linked.
    """
    jira = get_jira()
    try:
        jira.create_issue_link(link_type, inward, outward)
        logger.info(f'Issue link type "{link_type}" successfully created')
    except JIRAError:
        logger.exception(
            f'Error occurred during creating a link between "{outward}" '
            f'and "{inward}" issues using the type of link "{link_type}"'
        )


def get_jira_severity_field_id():
    """
    Return `id` of a field which name equals to `Severity`.
    """
    global severity_field_id
    if severity_field_id:
        return severity_field_id
    jira = get_jira()
    severity_fields = [f for f in jira.fields() if f["name"] == "Severity"]
    if severity_fields:
        severity_field_id = severity_fields[0]["id"]
    return severity_field_id
