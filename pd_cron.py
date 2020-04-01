import os
import datetime
from datetime import datetime, timedelta
import logging
import json

import db
import utils
import webhooks

INCIDENTS_ENDPOINT = 'incidents'
P1_PRIORITY_NAME = 'P1'
PAGERDUTY_CRON_SYNC_DAYS = os.environ['PAGERDUTY_CRON_SYNC_DAYS']
STATUS_RESOLVED = 'resolved'

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()


# Detect and synchronize PagerDuty incidents if user changes Priority field
# from non P-1 to P-1 value
# In this case application creates a corresponding JIRA issue the same way,
# if it would be created as P1 from the beginning.
def run(event=None, context=None, ):
    # current_time = datetime.datetime.now().time()
    # since=current_time - 7 day
    now = datetime.today()
    since = now.replace(minute=0, hour=0, second=0, microsecond=0) - \
            timedelta(days=int(PAGERDUTY_CRON_SYNC_DAYS))
    print(since)
    # logger.info("Your cron function ran at " + str(current_time))
    created = 0
    tracked = 0
    retrieved = 0
    more = True

    pagerduty = utils.get_pagerduty()
    for incident in pagerduty.iter_all(INCIDENTS_ENDPOINT, params={
            'since': since
        }):
        retrieved += 1
        incident_id = incident.get('id')
        logger.info(
            incident_id + ', #' + str(incident.get('incident_number')))
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
            if not priority_p1:
                db.put_cron_incident(incident_id, priority_name)
                tracked += 1
        elif existed_priority != priority_name and priority_p1:
            issue_key = db.get_issue_key_by_incident_id(incident_id)
            # do not create new issue in Jira if already created
            if issue_key is None:
                created += 1

                # NOTE
                # because of deprecated incident.description field (see
                # https://v2.developer.pagerduty.com/docs/webhooks-v2
                # -overview#incident-details for more info), both fields
                # currently are similar.
                webhooks.handle_triggered_incident(message={
                    'incident': incident,
                    'log_entries': [{
                        'channel': {
                            'summary': incident['title'],
                            'details': incident['description']
                        },
                    }]
                })
            # we don't keep P1 incidents in cron table
            db.delete_cron_entry_by_incident_id(incident_id)
    return {
        'retrieved': retrieved,
        'created': created,
        'tracked': tracked
    }
