import logging
import sys

from faker import Faker
from jira.exceptions import JIRAError
import json
import requests
from requests.auth import HTTPBasicAuth

from jpi import settings, utils


logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format=settings.LOGGING_FORMAT
)
[
    logging.getLogger(p).setLevel(logging.ERROR)
    for p in ["faker.factory", "urllib3"]
]
logger = logging.getLogger()
jira = utils.get_jira()
fake = Faker()
auth = HTTPBasicAuth(settings.JIRA_USER_EMAIL, settings.JIRA_API_TOKEN)

headers = {"Accept": "application/json", "Content-Type": "application/json"}


def create_issue_type(name, description="", issue_type_type="standard"):
    payload = json.dumps({
        "name": name,
        "description": description,
        "type": issue_type_type
    })

    response = requests.post(
        f"{settings.JIRA_API_URL}/issuetype",
        data=payload,
        headers=headers,
        auth=auth,
    )

    if not response.ok:
        response.raise_for_status()
    else:
        logger.info(f'Issue type "{name}" successfully created')


def create_project(key, name):
    """
    This method (as you can see) is implemented by means of `requests`
    but not `jira` library. I wasn't able to work around "You must
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

    template_key = "com.pyxis.greenhopper.jira:gh-simplified-kanban-classic"
    payload = json.dumps(
        {
            "name": name,
            "projectTypeKey": "software",
            "projectTemplateKey": template_key,
            "key": key,
            "leadAccountId": jira.myself()["accountId"],
        }
    )

    response = requests.post(
        f"{settings.JIRA_API_URL}/project",
        data=payload,
        headers=headers,
        auth=auth,
    )

    if not response.ok:
        response.raise_for_status()
    else:
        logger.info(f'Project "{name}" successfully created')

    return jira.project(key)


def create_issue(project_key, summary):
    issue_dict = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": project_key.title()},
    }
    try:
        issue = jira.create_issue(fields=issue_dict)
        logger.info(f'Issue "{issue.key}" successfully created')
    except JIRAError:
        logger.exception("Error occurred while creating an issue")


def create_issue_link_type(name, outward, inward):
    payload = json.dumps({"name": name, "outward": outward, "inward": inward})

    response = requests.post(
        f"{settings.JIRA_API_URL}/issueLinkType",
        data=payload,
        headers=headers,
        auth=auth,
    )

    if not response.ok:
        response.raise_for_status()
    else:
        logger.info(f'Issue link type "{name}" successfully created')


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

    for issue_link_type in jira.issue_link_types():
        if issue_link_type.name == settings.QUESTION_ISSUE_TYPE_NAME:
            msg = (
                f'Issue link type "{settings.QUESTION_ISSUE_TYPE_NAME}" '
                f"already exists. Skipping..."
            )
            logger.info(msg)
            break
    else:
        create_issue_link_type(
            settings.QUESTION_ISSUE_TYPE_NAME, "has question", "is question of"
        )

    for issue_link_type in jira.issue_link_types():
        if issue_link_type.name == settings.INCIDENT_MANAGER_ISSUE_TYPE_NAME:
            msg = 'Issue link type "{}" already exists. Skipping...'
            logger.info(msg.format(settings.INCIDENT_MANAGER_ISSUE_TYPE_NAME))
            break
    else:
        create_issue_link_type(
            settings.INCIDENT_MANAGER_ISSUE_TYPE_NAME,
            "has incident manager",
            "is incident manager of",
        )

    query = 'project={} and summary~"{}"'.format(
        settings.PERSON_PROJECT_KEY, settings.PAGERDUTY_USER_NAME
    )
    persons = jira.search_issues(query)
    if persons:
        msg = 'Person "{}" already exists. Skipping...'
        logger.info(msg.format(settings.PAGERDUTY_USER_NAME))
    else:
        issue_dict = {
            "project": {"key": settings.PERSON_PROJECT_KEY},
            "summary": settings.PAGERDUTY_USER_NAME,
            "issuetype": {"name": settings.PERSON_PROJECT_KEY.title()},
        }
        jira.create_issue(fields=issue_dict)
        logger.info(
            f'Person "{settings.PAGERDUTY_USER_NAME}" successfully created'
        )

    for issue_link_type in jira.issue_link_types():
        if issue_link_type.name == settings.TIMELINE_ISSUE_TYPE_NAME:
            msg = 'Issue link type "{}" already exists. Skipping...'
            logger.info(msg.format(settings.INCIDENT_MANAGER_ISSUE_TYPE_NAME))
            break
    else:
        create_issue_link_type(
            settings.TIMELINE_ISSUE_TYPE_NAME, "has timeline", "is timeline of"
        )

    for issue_link_type in jira.issue_link_types():
        if issue_link_type.name == settings.STAKEHOLDER_ISSUE_TYPE_NAME:
            msg = 'Issue link type "{}" already exists. Skipping...'
            logger.info(msg.format(settings.STAKEHOLDER_ISSUE_TYPE_NAME))
            break
    else:
        create_issue_link_type(
            settings.STAKEHOLDER_ISSUE_TYPE_NAME,
            "has stakeholder",
            "is stakeholder of",
        )
