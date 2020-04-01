from datetime import datetime, timedelta
import datetime
import logging
import os

import db
import utils
import webhooks

INCIDENTS_ENDPOINT = 'incidents'
P1_PRIORITY_NAME = 'P1'
PAGERDUTY_CRON_SYNC_DAYS = os.environ['PAGERDUTY_CRON_SYNC_DAYS']
STATUS_RESOLVED = 'resolved'

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
        priority = incident.get('priority')
        if not priority:
            continue
        priority_name = priority.get('name')
        priority_p1 = priority_name == P1_PRIORITY_NAME
        existed_priority = db.get_priority_by_incident_id(incident_id)
        if not existed_priority:
            # we keep only non-P1 incidents in the cron table
            if not priority_p1:
                db.put_low_prio_incident(incident_id, priority_name)
                tracked += 1
                logger.info('Start tracking {} (#{}) incident.'.format(
                    incident_id, incident.get('incident_number')
                ))
        elif existed_priority != priority_name and priority_p1:
            # A situation, if user changing the priority several times. P2-> P1
            # -> P2 -> P1. This additional checking will prevent re-posting the
            # issue in JIRA.
            issue_key = db.get_issue_key_by_incident_id(incident_id)
            if issue_key is None:
                summary = incident['title']
                description = summary
                log_entries_ep = '/incidents/{}/log_entries'.format(incident_id)
                for entry in pagerduty.rget(log_entries_ep, params={
                    'include[]': ['channels']
                }):
                    channel = entry['channel']
                    if channel:
                        description = channel['details']
                        if description:
                            break
                else:
                    logger.error(
                        'For Incident {} (#{}) field description is not '
                        'accessible! '.format(
                            incident_id, incident.get('incident_number')
                        ))
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
                logger.info('For Incident {} (#{}) issue {} created! '.format(
                    incident_id, incident.get('incident_number'), issue_key
                ))
            # remove, as far as we don't keep P1 incidents in the cron table
            db.delete_low_prio_incident_by_incident_id(incident_id)
    return {
        'retrieved': retrieved,
        'created': created,
        'tracked': tracked
    }
