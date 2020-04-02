import datetime
from datetime import datetime, timedelta
import logging
import os

import db
import utils
import webhooks

INCIDENTS_ENDPOINT = 'incidents'
P1_PRIORITY_NAME = 'P1'
PAGERDUTY_CRON_SYNC_DAYS = os.environ['PAGERDUTY_CRON_SYNC_DAYS']
STATUS_RESOLVED = 'resolved'
ISSUE_KEY_FIELD = 'issue_key'

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a
    # handler is already configured, `.basicConfig` does not execute. Thus we
    # set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()


def run():
    """
    Detect and synchronize PagerDuty incidents, if user changes Priority field
    from non P-1 to P-1 value. In this case application creates a
    corresponding JIRA issue the same way, if it would be created as P1 from
    the beginning.
    """
    now = datetime.today()
    since = now.replace(minute=0, hour=0, second=0, microsecond=0) - \
            timedelta(days=int(PAGERDUTY_CRON_SYNC_DAYS))
    created = 0
    tracked = 0
    retrieved = 0

    pagerduty = utils.get_pagerduty()
    for incident in pagerduty.iter_all(INCIDENTS_ENDPOINT, params={
        'since': since
    }):
        retrieved += 1
        incident_id = incident.get('id')
        resolved = incident['status'] == STATUS_RESOLVED
        if resolved:
            continue
        fields = {}
        priority = incident.get('priority')
        high_priority = False
        priority_name = None
        if priority:
            priority_name = priority.get('name')
            if priority_name:
                fields['priority'] = priority_name
                high_priority = priority_name == P1_PRIORITY_NAME
        db_incident = db.get_incident_by_id(incident_id, resolved=True)
        if not db_incident:
            fields['incident_number'] = incident.get('incident_number')
            db.put_incident(incident_id, fields)
            tracked += 1
            logger.info('Start tracking {} (#{}) incident.'.format(
                incident_id, incident.get('incident_number')
            ))
        elif not db_incident.get('resolved'):
            db_priority = db_incident.get('priority')
            db_jira = db_incident.get(ISSUE_KEY_FIELD)
            if high_priority and db_priority != priority_name and not db_jira:
                issue_key = incident.get(ISSUE_KEY_FIELD)
                if not issue_key:
                    number = incident.get('incident_number')
                    summary = incident['title']
                    description = summary
                    endpoint = '/incidents/{}/log_entries'.format(incident_id)
                    for entry in pagerduty.rget(endpoint, params={
                        'include[]': ['channels']
                    }):
                        description = entry.get('channel', {}).get('details')
                        if description:
                            break
                    else:
                        logger.warning(f'Incident {incident_id} (#{number})'
                                     f' field description is empty')
                    created += 1
                    issue_key = webhooks.handle_triggered_incident(message={
                        'incident': incident,
                        'log_entries': [{
                            'channel': {
                                'summary': summary,
                                'details': description
                            },
                        }]
                    })
                    logger.info(f'Incident {incident_id} (#{number}): '
                                f'JIRA issue {issue_key} created! ')

    return {
        'retrieved': retrieved,
        'created': created,
        'tracked': tracked
    }
