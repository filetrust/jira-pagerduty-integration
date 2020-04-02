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
        if incident_id:
            pagerduty = utils.get_pagerduty()
            try:
                pagerduty.rput(INCIDENT_ENDPOINT, json=[{
                    'id': incident_id, 'type': 'incident', 'status': 'resolved'
                }])
                db.resolve_incident(incident_id)
            except Exception as e:
                # logger.error
                pass
