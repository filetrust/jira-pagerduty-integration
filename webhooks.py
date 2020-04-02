import os
import db
import utils
from jira.exceptions import JIRAError

P1_PRIORITY_NAME = 'P1'
ISSUE_KEY_NAME = 'issueKey'
severity_field_id = None


def handle_triggered_incident(message):
    global severity_field_id
    incident = message.get('incident', {})
    incident_id = incident['id']
    issue_key = None
    priority = incident.get('priority')
    high_priority = False
    incident_fields = {}
    if priority:
        priority_name = priority.get('name')
        if priority_name:
            incident_fields['priority'] = priority_name
            high_priority = priority_name == P1_PRIORITY_NAME
    if high_priority:
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
            issue_key = issue.key
            incident_fields[ISSUE_KEY_NAME] = issue_key
    db.put_incident(incident_id, incident_fields)
    return issue_key


def handle_resolved_incident(message):
    incident = message.get('incident')
    incident_id = incident['id']
    issue_key = db.get_issue_key_by_incident_id(incident_id)
    if issue_key:
        jira = utils.get_jira()
        issue = jira.issue(issue_key)
        done_transition_ids = [
            t['id'] for t in jira.transitions(issue) if t['name'] == 'Done']
        if done_transition_ids:
            try:
                jira.transition_issue(issue, done_transition_ids[0])
                db.resolve_incident(incident_id)
            except JIRAError as e:
                # logger.error
                pass
        else:
            # logger.warn('JIRA repo has no Done state !?)'
            pass


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
