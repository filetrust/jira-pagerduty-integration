from datetime import datetime, timedelta
import logging
import os

import db
import utils
import webhooks

INCIDENTS_ENDPOINT = "incidents"
P1_PRIORITY_NAME = "P1"
PAGERDUTY_CRON_SYNC_DAYS = os.environ["PAGERDUTY_CRON_SYNC_DAYS"]
STATUS_RESOLVED = "resolved"

RESOLVED_FIELD_NAME = "resolved"
ISSUE_KEY_FIELD = "issue_key"
INCIDENT_NUMBER_FIELD_NAME = "incident_number"

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a
    # handler is already configured, `.basicConfig` does not execute. Thus we
    # set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()


def run(event, context):
    """
    Detect and synchronize PagerDuty incidents, if user changes Priority field
    from non P-1 to P-1 value. In this case application creates a
    corresponding JIRA issue the same way, if it would be created as P1 from
    the beginning.
    """
    now = datetime.today()
    since = now.replace(minute=0, hour=0, second=0, microsecond=0) - timedelta(
        days=int(PAGERDUTY_CRON_SYNC_DAYS)
    )
    created = 0
    tracked = 0
    retrieved = 0
    changed = 0

    pagerduty = utils.get_pagerduty()
    for incident in pagerduty.iter_all(
        INCIDENTS_ENDPOINT, params={"since": since}
    ):
        retrieved += 1
        incident_id = incident.get("id")
        resolved = incident["status"] == STATUS_RESOLVED
        if resolved:
            continue
        fields = {}
        priority = incident.get("priority")
        high_priority = False
        priority_name = None
        if priority:
            priority_name = priority.get("name")
            if priority_name:
                fields["priority"] = priority_name
                high_priority = priority_name == P1_PRIORITY_NAME
        db_incident = db.get_incident_by_id(incident_id, resolved=True)
        if not db_incident:
            fields[INCIDENT_NUMBER_FIELD_NAME] = incident.get(
                INCIDENT_NUMBER_FIELD_NAME
            )
            db.put_incident(incident_id, fields)
            tracked += 1
            logger.info(
                "Start tracking {} (#{}) incident.".format(
                    incident_id, incident.get(INCIDENT_NUMBER_FIELD_NAME)
                )
            )
        elif not db_incident.get(RESOLVED_FIELD_NAME):
            db_priority = db_incident.get("priority")
            db_issue_key = db_incident.get(ISSUE_KEY_FIELD)
            if (
                high_priority
                and db_priority != priority_name
                and not db_issue_key
            ):
                issue_key = incident.get(ISSUE_KEY_FIELD)
                if not issue_key:
                    number = incident.get(INCIDENT_NUMBER_FIELD_NAME)
                    summary = incident["title"]
                    description = summary
                    agent = ""
                    endpoint = "/incidents/{}/log_entries".format(incident_id)
                    for entry in pagerduty.rget(
                        endpoint, params={"include[]": ["channels"]}
                    ):
                        if not description:
                            description = entry.get("channel", {}).get(
                                "details"
                            )
                        if not agent:
                            agent = entry.get("agent", {}).get("summary")
                    else:
                        logger.warning(
                            f"Incident {incident_id} (#{number})"
                            f" field description is empty"
                        )
                    created += 1
                    issue_key = webhooks.handle_triggered_incident(
                        message={
                            "incident": incident,
                            "log_entries": [
                                {
                                    "channel": {
                                        "summary": summary,
                                        "details": description,
                                    },
                                    "agent": {"summary": agent},
                                }
                            ],
                        }
                    )
                    logger.info(
                        f"Incident {incident_id} (#{number}): "
                        f"JIRA issue {issue_key} created!"
                    )
            elif db_priority != priority_name:
                # just update priority
                changed += 1
                db.put_incident(incident_id, {"priority": priority_name})

    return {
        "retrieved": retrieved,
        "created": created,
        "changed": changed,
        "tracked": tracked,
    }
