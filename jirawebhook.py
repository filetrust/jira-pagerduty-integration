import os

import db
import utils

INCIDENT_ENDPOINT = 'incidents'


def jira(event):
    """
    A webhook function which basically triggered by changing the JIRA Ticket
    to Done state.
    """
    changelog = event.get('changelog', {})
    changes = changelog.get('items', [{}])

    has_done = False
    for item in changes:
        if item.get('fieldId') == 'status' and item.get('toString') == 'Done':
            has_done = True
            break
    issue_key = None
    if has_done:
        issue_key = event.get('issue', {}).get('key')
    if issue_key is not None:
        incident_id = db.get_incident_id_by_issue_key(issue_key)
        if incident_id is not None:
            pagerduty = utils.get_pagerduty()
            db.delete_relation_by_incident_id(incident_id)
            try:
                pagerduty.rput(INCIDENT_ENDPOINT, json=[{
                    'id': incident_id, 'type': 'incident', 'status': 'resolved'
                }])
            except Exception as e:
                # Restore relation if something goes wrong
                is_exists = db.get_incident_id_by_issue_key(issue_key)
                if is_exists is None:
                    db.put_incident_issue_relation(incident_id, issue_key)
                raise e
