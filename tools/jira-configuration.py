import logging
import os
import re
import sys

from faker import Faker
from jira.exceptions import JIRAError
import json
import requests
from requests.auth import HTTPBasicAuth

import utils


QUESTION_ISSUE_TYPE_NAME = 'Question'
FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
JIRA_SERVER_URL = os.environ['JIRA_SERVER_URL']
JIRA_API_URL =  f'{JIRA_SERVER_URL}/rest/api/3'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=FORMAT)
[
 logging.getLogger(p).setLevel(logging.ERROR)
 for p in ['faker.factory', 'urllib3']
]
logger = logging.getLogger()
jira = utils.get_jira()
fake = Faker()
auth = HTTPBasicAuth(
    os.environ['JIRA_USER_EMAIL'], os.environ['JIRA_API_TOKEN'])

headers = {
   'Accept': 'application/json',
    'Content-Type': 'application/json',
}


def create_project(key, name):
    """
    This method (as you can see) is implemented by means of `requests`
    but not `jira` library. I wasn't able to work arround "You must
    specify a valid project lead" error while creating a project.
    """
    project = None
    try:
        project = jira.project(key)
    except JIRAError as error:
        if error.status_code == 404:
            pass
        else:
            raise

    if project:
        logger.info(f'Project "{name}" already exists. Skipping...')
        return project

    payload = json.dumps({
        'name': name,
        'projectTypeKey': 'software',
        'projectTemplateKey': 'com.pyxis.greenhopper.jira:gh-simplified-kanban-classic',
        'key': key,
        'leadAccountId': jira.myself()['accountId'],
    })

    response = requests.post(
       f'{JIRA_API_URL}/project',
       data=payload,
       headers=headers,
       auth=auth
    )

    if not response.ok:
        response.raise_for_status()
    else:
        logger.info(f'Project "{name}" successfully created')

    return jira.project(key)


def create_issue(project_key, summary):
    issue_dict = {
        'project': {'key': project_key},
        'summary': summary,
        'issuetype': {'name': 'Bug'},
    }
    try:
        issue = jira.create_issue(fields=issue_dict)
        logger.info(f'Issue "{issue.key}" successfully created')
    except JIRAError as error:
        logger.exception('Error occurred while creating an issue')


def create_issue_link_type(name, outward, inward):
    payload = json.dumps({
        'name': name,
        'outward': outward,
        'inward': inward,
    })

    response = requests.post(
       f'{JIRA_API_URL}/issueLinkType',
       data=payload,
       headers=headers,
       auth=auth
    )

    if not response.ok:
        response.raise_for_status()
    else:
        logger.info(f'Issue link type "{name}" successfully created')


if __name__ == "__main__":
    person_project_key = 'PERSON'
    project = create_project(person_project_key, 'Persons')
    if project:
        create_issue(person_project_key, fake.name())
        create_issue(person_project_key, fake.name())
        create_issue(person_project_key, fake.name())

    incident_project_key = 'INCIDENT'
    project = create_project(incident_project_key, 'Incidents')
    if project:
        create_issue(incident_project_key, fake.sentence())
        create_issue(incident_project_key, fake.sentence())
        create_issue(incident_project_key, fake.sentence())

    question_project_key = 'QUESTION'
    project = create_project(question_project_key, 'Questions')
    if project:
        create_issue(question_project_key, fake.sentence())
        create_issue(question_project_key, fake.sentence())
        create_issue(question_project_key, fake.sentence())

    for issue_link_type in jira.issue_link_types():
        if issue_link_type.name == QUESTION_ISSUE_TYPE_NAME:
            msg = (
                f'Issue link type "{QUESTION_ISSUE_TYPE_NAME}" '
                f'already exists. Skipping...'
            )
            logger.info(msg)
            break
    else:
        create_issue_link_type(
            QUESTION_ISSUE_TYPE_NAME, 'has question', 'is question of')
