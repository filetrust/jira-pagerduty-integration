import logging
import os

from jira import JIRA
from jira.exceptions import JIRAError
from pdpyras import APISession


jira = None
pagerduty = None
logger = logging.getLogger()


def get_jira():
    global jira
    if jira is None:
        options = {
            'server': os.environ['JIRA_SERVER_URL'],
        }
        basic_auth = (
            os.environ['JIRA_USER_EMAIL'],
            os.environ['JIRA_API_TOKEN'],
        )
        jira = JIRA(options, basic_auth=basic_auth)
    return jira


def get_pagerduty():
    global pagerduty
    if pagerduty is None:
        api_token = os.environ['PAGERDUTY_API_TOKEN']
        user_email_from = os.environ['PAGERDUTY_USER_EMAIL']
        pagerduty = APISession(api_token, default_from=user_email_from)
    return pagerduty


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
    except JIRAError as error:
        logger.exception(
            f'Error occurred during creating a link between "{outward}" '
            f'and "{inward}" issues using the type of link "{link_type}"'
        )
