import argparse
import logging
import sys

from faker import Faker
from requests.exceptions import HTTPError

from jpi import settings
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


def create_issue_type(name, description="", issue_type_type="standard"):
    issue_type = None
    try:
        issue_type = jira.create_issue_type(name, description, issue_type_type)
        logger.info(f'Issue type "{name}" successfully created')
    except HTTPError as error:
        if error.response.status_code == 409:
            logger.info(f'Issue type "{name}" already exists. Skipping...')
        else:
            logger.exception("Error occurred while creating an issue")
    return issue_type


def create_project(key, name):
    """
    This method (as you can see) is implemented by means of `requests`
    but not `jira` library. I wasn't able to work around "You must
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
        "issuetype": {"name": project_key.title()},
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


def step1():
    for project_key in settings.GLASSWALL_JIRA_PROJECT_KEYS:
        issue_type_key = project_key.title()
        create_project(project_key, f'{issue_type_key}s')
        create_issue_type(
            issue_type_key,
            description=f"Corresponding to Glasswall {issue_type_key}"
        )


def step2():
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

    if not settings.PAGERDUTY_USER_NAME:
        msg = (
            "`PAGERDUTY_USER_NAME` setting is not defined. "
            "It should be provided via an environment variable."
        )
        raise Exception(msg)
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
            "issuetype": {"name": settings.PERSON_PROJECT_KEY.title()},
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


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Jira configuration tool.')
    parser.add_argument('-s', '--step', dest='step', type=int, required=True)

    args = parser.parse_args()

    if args.step == 1:
        step1()
    elif args.step == 2:
        step2()
    else:
        raise Exception('Invalid step number. Allowed values: 1 and 2')
