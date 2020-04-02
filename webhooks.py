import logging
import os

from jira.exceptions import JIRAError

import db
import utils

P1_PRIORITY_NAME = 'P1'
PERSON_PROJECT_KEY = os.environ['PERSON_PROJECT_KEY']
severity_field_id = None
logger = logging.getLogger()


def link_issue(outward, inward, link_type):
    """
    Create a link between two issues. `inward` is an issue to link
    from, `outward` is an issue to link to and `link_type` is the type
    of link to create. `inward` and `outward` are the keys of the
    issues that are being linked.
    """
    jira = utils.get_jira()
    try:
        jira.create_issue_link(link_type, inward, outward)
        logger.info(f'Issue link type "{link_type}" successfully created')
    except JIRAError as error:
        logger.exception(
            f'Error occurred during creating a link between "{outward}" '
            f'and "{inward}" issues using the type of link "{link_type}"'
        )


def handle_triggered_incident(message):
    global severity_field_id
    incident = message.get('incident', {})
    if incident.get('priority', {}).get('name') != P1_PRIORITY_NAME:
        # Skip all incidents except with P1 priority.
        return
    jira = utils.get_jira()
    if severity_field_id is None:
        fields = jira.fields()
        severity_fields = [f for f in fields if f['name'] == 'Severity']
        severity_field_id = severity_fields[0]['id']
    entries = message.get('log_entries', [])
    severity_field_value = 'SEV-0'
    for entry in entries:
        issue_dict = {
            'project': {'key': os.environ['JIRA_PROJECT_KEY']},
            'summary': entry['channel']['summary'],
            'description': entry['channel']['details'],
            'issuetype': {'name': 'Bug'},
            'priority': {'name': 'Highest'},
        }
        if severity_field_id:
            issue_dict[severity_field_id] = {'value': severity_field_value}
        issue = jira.create_issue(fields=issue_dict)
        db.put_incident_issue_relation(incident['id'], issue.key)
        questions = os.environ.get('JIRA_ISSUE_QUESTIONS', '')
        questions = [q for q in questions.split(',') if q]
        for q in questions:
            link_issue(q, issue.key, 'has question')
        assignee = entries[0]['agent']['summary']
        persons = jira.search_issues(
            f'project={PERSON_PROJECT_KEY} and summary~"{assignee}"')
        if persons:
            link_issue(persons[0].key, issue.key, 'has incident manager')


def handle_resolved_incident(message):
    incident = message.get('incident')
    issue_key = db.get_issue_key_by_incident_id(incident['id'])
    if issue_key is not None:
        jira = utils.get_jira()
        issue = jira.issue(issue_key)
        done_transition_ids = [
            t['id'] for t in jira.transitions(issue) if t['name'] == 'Done']
        db.delete_relation_by_issue_key(issue_key)
        if done_transition_ids:
            try:
                jira.transition_issue(issue, done_transition_ids[0])
            except Exception as e:
                # Restore relation if something goes wrong
                is_exists = db.get_issue_key_by_incident_id(incident['id'])
                if is_exists is None:
                    db.put_incident_issue_relation(incident['id'], issue_key)
                raise e


def pagerduty(event):
    """
    A webhook that should be used by PagerDuty.
    """
    messages = event.get('messages', [])
    for message in messages:
        if message.get('event') == 'incident.trigger':
            handle_triggered_incident(message)
        elif message.get('event') == 'incident.resolve':
            handle_resolved_incident(message)
