import json
import logging
import os
from requests.exceptions import HTTPError

from pdpyras import APISession

from jpi import settings, db
from jpi.api import jira


pagerduty = None
questions = None
severity_field_id = None
logger = logging.getLogger()


def get_pagerduty():
    global pagerduty
    if pagerduty is None:
        pagerduty = APISession(
            settings.PAGERDUTY_API_TOKEN,
            default_from=settings.PAGERDUTY_USER_EMAIL,
        )
    return pagerduty


def get_questions():
    global questions
    if questions is None:
        questions_file = os.path.join(
            settings.PROJECT_PATH, settings.QUESTIONS_FILE
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
    try:
        jira.create_issue_link(link_type, inward, outward)
        logger.info(f'Issue link type "{link_type}" successfully created')
    except HTTPError:
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
    severity_fields = [
        f for f in jira.get_fields()
        if f["name"] == settings.JIRA_SEVERITY_FIELD_NAME
    ]
    if severity_fields:
        severity_field_id = severity_fields[0]["id"]
    return severity_field_id


def get_incident_manager(fullname):
    """
    Return an incident manager by his/her full name.
    """
    persons = jira.search_issues(
        f'project={settings.PERSON_PROJECT_KEY} and summary~"{fullname}"'
    )
    if persons['issues']:
        return persons['issues'][0]


def create_jira_incident(summary, description=None, incident_manager=None):
    """
    Create Jira issue in project with key `INCIDENT`.
    """
    fields = {
        "project": {"key": settings.INCIDENT_PROJECT_KEY},
        "summary": summary,
        "issuetype": {"name": "Bug"},
        "priority": {"name": "Highest"},
    }
    if description:
        fields['description'] = description
    severity_field_id = get_jira_severity_field_id()
    if severity_field_id:
        fields[severity_field_id] = {
            "value": settings.JIRA_INCIDENT_SEVERITY
        }
    issue = jira.create_issue(fields)
    for q in get_questions():
        fields = {
            "project": {"key": settings.QUESTION_PROJECT_KEY},
            "summary": q["summary"],
            "description": q["description"],
            "issuetype": {"name": "Bug"},
        }
        question = jira.create_issue(fields)
        link_issue(
            question['key'], issue['key'], settings.QUESTION_ISSUE_TYPE_NAME)
    stakeholders = settings.JIRA_ISSUE_STAKEHOLDERS
    stakeholders = [q for q in stakeholders.split(",") if q]
    for s in stakeholders:
        link_issue(s, issue['key'], settings.STAKEHOLDER_ISSUE_TYPE_NAME)
    if incident_manager:
        link_issue(
            incident_manager['key'],
            issue['key'],
            settings.INCIDENT_MANAGER_ISSUE_TYPE_NAME
        )
    return issue


def resolve_incident(incident_id):
    db.put_incident(incident_id, {settings.RESOLVED_FIELD_NAME: db.get_now()})


def last_polling_timestamp():
    return db.get_config_parameter(settings.LAST_POLLING_TIMESTAMP_PARAM)


def update_polling_timestamp(timestamp):
    return db.update_config_parameter(
        settings.LAST_POLLING_TIMESTAMP_PARAM, timestamp
    )
