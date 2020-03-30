import os

from jira import JIRA
from pdpyras import APISession


jira = None
pagerduty = None


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
