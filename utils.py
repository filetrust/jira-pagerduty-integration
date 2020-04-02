import json
import logging
import os

from jira import JIRA
from pdpyras import APISession


jira = None
pagerduty = None
questions = None
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


def get_questions():
    global questions;
    if questions is None:
        questions_file = os.environ['QUESTIONS_FILE']
        try:
            with open(questions_file, 'r') as f:
                questions = json.loads(f.read())
        except Exception as error:
            questions = []
            logger.exception(
                f'Error occurred while reading the predefined '
                f'questions from the file: {questions_file}'
            )
    return questions
