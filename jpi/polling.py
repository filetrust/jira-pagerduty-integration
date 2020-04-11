import datetime
import logging
import os
import pytz

from jira.exceptions import JIRAError
from pdpyras import PDClientError

from jpi import db, utils, webhooks

LOG_ENTRIES_ENDPOINT = "/log_entries"
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TIMELINE_PROJECT_KEY = os.environ["TIMELINE_PROJECT_KEY"]


def polling_handler(event, context):
    result = {"ok": True}
    timeline = 0
    pagerduty = utils.get_pagerduty()
    jira = utils.get_jira()
    polling_timestamp = db.last_polling_timestamp()
    if not polling_timestamp:
        poll_past_hours = int(os.environ.get("LOG_ENTRIES_POLL_PAST_HOURS"))
        now = datetime.datetime.now(pytz.utc)
        ts = now - datetime.timedelta(hours=poll_past_hours)
    else:
        ts = datetime.datetime.strptime(
            polling_timestamp, "%Y-%m-%d %H:%M:%S.%f%z"
        )

    params = {"since": str(ts)}
    processing_timestamp = db.get_now()
    try:
        log_entries = list(
            pagerduty.iter_all(LOG_ENTRIES_ENDPOINT, params=params)
        )
    except PDClientError:
        msg = "Error reading Log Entries from PagerDuty instance"
        result["ok"] = False
        result["error"] = msg
        logger.exception(msg)
    else:
        logger.info("{} log entries found".format(len(log_entries)))
        for log_entry in log_entries:
            if db.get_log_entry_by_id(log_entry["id"]):
                # Usually should not happens as far as we read items from
                # our last polling call
                msg = "[{}] Existing log entry found. Skipping..."
                msg = msg.format(log_entry["id"])
                logger.info(msg)
                continue
            if log_entry["type"] == "status_update_log_entry":
                logger.info(
                    "[{}] New status update found".format(log_entry["id"])
                )
                issue_key = db.get_issue_key_by_incident_id(
                    log_entry["incident"]["id"]
                )
                if issue_key:
                    logger.info(
                        "[{}] Related issue found: {}".format(
                            log_entry["id"], issue_key
                        )
                    )
                    try:
                        jira.issue(issue_key)
                    except JIRAError:
                        msg = "[{}] Error occurred while retrieving Jira issue"
                        msg = msg.format(log_entry["id"])
                        logger.exception(msg)
                        result["ok"] = False
                        result["error"] = msg
                        continue

                    issue_dict = {
                        "project": {"key": os.environ["TIMELINE_PROJECT_KEY"]},
                        "summary": log_entry["message"],
                        "issuetype": {"name": "Bug"},
                    }
                    try:
                        timeline_issue = jira.create_issue(fields=issue_dict)
                        logger.info(
                            'Timeline issue "{}" successfully created'.format(
                                timeline_issue.key
                            )
                        )
                        utils.link_issue(
                            timeline_issue.key, issue_key, "has timeline"
                        )
                        timeline += 1
                    except JIRAError:
                        msg = "[{}] Error creating timeline link to JIRA {}"
                        msg = msg.format(issue_key)
                        logger.exception(msg)
                        result["ok"] = False
                        result["error"] = msg
                else:
                    logger.info(
                        "[{}] Issue key not found".format(log_entry["id"])
                    )

            db.put_log_entry(log_entry["id"])

    # anyway put last timestamp the the db at the end of last issues polling
    db.update_polling_timestamp(processing_timestamp)

    return {
        **result,
        **{
            "timeline": timeline
        }
    }


INCIDENTS_ENDPOINT = "incidents"
P1_PRIORITY_NAME = "P1"
PAGERDUTY_CRON_SYNC_DAYS = os.environ["PAGERDUTY_CRON_SYNC_DAYS"]
STATUS_RESOLVED = "resolved"

RESOLVED_FIELD_NAME = "resolved"
ISSUE_KEY_FIELD = "issue_key"
INCIDENT_NUMBER_FIELD_NAME = "incident_number"


def cron_handler(event, context):
    """
    Detect and synchronize PagerDuty incidents, if user changes Priority field
    from non P-1 to P-1 value. In this case application creates a
    corresponding JIRA issue the same way, if it would be created as P1 from
    the beginning.
    """

    result = {"ok": True}
    now = datetime.datetime.today()
    since = now.replace(minute=0, hour=0, second=0, microsecond=0
    ) - datetime.timedelta(days=int(PAGERDUTY_CRON_SYNC_DAYS))

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
        **result,
        **{
            "retrieved": retrieved,
            "created": created,
            "changed": changed,
            "tracked": tracked,
        }
    }


def handler(event, context):
    polling_result = polling_handler(event, context)
    cron_result = cron_handler(event, context)
    result = {**polling_result, **cron_result}
    if not polling_result.get("ok") or not cron_result.get("ok"):
        result["ok"] = False
        if not polling_result.get("ok"):
            result["polling_ok"] = polling_result.get("ok")
            result["polling_error"] = polling_result.get("error")
        if not cron_result.get("ok"):
            result["cron_ok"] = cron_result.get("ok")
            result["cron_error"] = cron_result.get("error")

    return result
