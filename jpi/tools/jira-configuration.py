import logging
import sys

from faker import Faker
import json
import requests
from requests.exceptions import HTTPError

from jpi import settings, utils
from jpi.api import jira


logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format=settings.LOGGING_FORMAT
)
[
    logging.getLogger(p).setLevel(logging.ERROR)
    for p in ["faker.factory", "urllib3"]
]
logger = logging.getLogger()
fake = Faker()


def create_project(key, name):
    """
    This method (as you can see) is implemented by means of `requests`
    but not `jira` library. I wasn't able to work arround "You must
    specify a valid project lead" error while creating a project.
    """
    project = None
    try:
        project = jira.get_project(key)
    except HTTPError as error:
        if error.response.status_code == 404:
            pass
        else:
            raise

    if project:
        logger.info(f'Project "{name}" already exists. Skipping...')
        return project

    jira.create_project(key, name)
    logger.info(f'Project "{name}" successfully created')

    return jira.get_project(key)


def create_issue(project_key, summary):
    issue_dict = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": "Bug"},
    }
    try:
        issue = jira.create_issue(fields=issue_dict)
        issue_key = issue['key']
        logger.info(f'Issue "{issue_key}" successfully created')
    except HTTPError:
        logger.exception("Error occurred while creating an issue")


def create_issue_link_type(issue_link_type, outward, inward):
    for link_type in jira.get_issue_link_types():
        if link_type['name'] == issue_link_type:
            msg = (
                f'Issue link type "{issue_link_type}" '
                f"already exists. Skipping..."
            )
            logger.info(msg)
            break
    else:
        jira.create_issue_link_type(issue_link_type, outward, inward)
        logger.info(f'Issue link type "{issue_link_type}" created')


if __name__ == "__main__":
    project = create_project(settings.PERSON_PROJECT_KEY, "Persons")
    if project:
        create_issue(settings.PERSON_PROJECT_KEY, fake.name())
        create_issue(settings.PERSON_PROJECT_KEY, fake.name())
        create_issue(settings.PERSON_PROJECT_KEY, fake.name())

    project = create_project(settings.INCIDENT_PROJECT_KEY, "Incidents")
    if project:
        create_issue(settings.INCIDENT_PROJECT_KEY, fake.sentence())
        create_issue(settings.INCIDENT_PROJECT_KEY, fake.sentence())
        create_issue(settings.INCIDENT_PROJECT_KEY, fake.sentence())

    project = create_project(settings.QUESTION_PROJECT_KEY, "Questions")
    if project:
        create_issue(settings.QUESTION_PROJECT_KEY, fake.sentence())
        create_issue(settings.QUESTION_PROJECT_KEY, fake.sentence())
        create_issue(settings.QUESTION_PROJECT_KEY, fake.sentence())

    project = create_project(settings.TIMELINE_PROJECT_KEY, "Timeline")
    if project:
        create_issue(settings.TIMELINE_PROJECT_KEY, fake.sentence())
        create_issue(settings.TIMELINE_PROJECT_KEY, fake.sentence())
        create_issue(settings.TIMELINE_PROJECT_KEY, fake.sentence())

    create_issue_link_type(
        settings.QUESTION_ISSUE_TYPE_NAME, "has question", "is question of")
    create_issue_link_type(
        settings.INCIDENT_MANAGER_ISSUE_TYPE_NAME,
        "has incident manager",
        "is incident manager of"
    )

    query = 'project={} and summary~"{}"'.format(
        settings.PERSON_PROJECT_KEY, settings.PAGERDUTY_USER_NAME
    )
    persons = jira.search_issues(query)
    if persons['issues']:
        msg = 'Person "{}" already exists. Skipping...'
        logger.info(msg.format(settings.PAGERDUTY_USER_NAME))
    else:
        fields = {
            "project": {"key": settings.PERSON_PROJECT_KEY},
            "summary": settings.PAGERDUTY_USER_NAME,
            "issuetype": {"name": "Story"},
        }
        jira.create_issue(fields)
        logger.info(
            f'Person "{settings.PAGERDUTY_USER_NAME}" successfully created'
        )

    create_issue_link_type(
        settings.TIMELINE_ISSUE_TYPE_NAME,
        "has timeline",
        "is timeline of"
    )

    create_issue_link_type(
        settings.STAKEHOLDER_ISSUE_TYPE_NAME,
        "has stakeholder",
        "is stakeholder of"
    )
