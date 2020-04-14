import datetime
import logging
import re
from requests.exceptions import HTTPError

from pdpyras import PDClientError
import pytz

from jpi import db, settings, utils
from jpi.api import jira

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handle_priority_change_log_entry(log_entry):
    pattern = re.compile(r'Priority changed from "P\d" to "P1"')
    if pattern.match(log_entry["summary"]):
        logger.info("[{}] {}".format(log_entry["id"], log_entry["summary"]))
        agent = log_entry["agent"]
        incident = log_entry["incident"]
        issue_key = db.get_issue_key_by_incident_id(incident["id"])
        incident_fields = {
            "priority": log_entry["channel"]["new_priority"]["summary"]
        }
        if not issue_key:
            # Issue doesn't exist, let's create it.
            incident_manager = utils.get_incident_manager(agent["summary"])
            issue = utils.create_jira_incident(
                incident["summary"], incident_manager=incident_manager
            )
            incident_fields[settings.ISSUE_KEY_FIELD_NAME] = issue.key
        db.put_incident(incident["id"], incident_fields)


def handle_log_entry(log_entry):
    logger.info("[{}] New log entry found".format(log_entry["id"]))

    if log_entry["type"] == "priority_change_log_entry":
        logger.info("[{}] Priority changed".format(log_entry["id"]))
        handle_priority_change_log_entry(log_entry)

    issue_key = db.get_issue_key_by_incident_id(log_entry["incident"]["id"])
    if issue_key:
        logger.info(
            "[{}] Related issue found: {}".format(log_entry["id"], issue_key)
        )
        try:
            jira.get_issue(issue_key)
        except HTTPError:
            msg = "[{}] Error occurred while retrieving Jira issue"
            logger.exception(msg.format(log_entry["id"]))
            return

        fields = {
            "project": {"key": settings.TIMELINE_PROJECT_KEY},
            "summary": log_entry["summary"],
            "issuetype": {"name": "Bug"},
        }
        try:
            timeline_issue = jira.create_issue(fields)
            logger.info(
                'Timeline issue "{}" successfully created'.format(
                    timeline_issue['key']
                )
            )
            utils.link_issue(
                timeline_issue['key'],
                issue_key,
                settings.TIMELINE_ISSUE_TYPE_NAME
            )
        except HTTPError:
            msg = "[{}] Error creating timeline link to Jira issue {}"
            logger.exception(msg.format(issue_key))
            return
        db.put_log_entry(log_entry["id"])
    else:
        logger.info("[{}] Issue key not found".format(log_entry["id"]))


def handler(event, context):
    result = {"ok": True}
    pagerduty = utils.get_pagerduty()
    polling_timestamp = utils.last_polling_timestamp()
    if not polling_timestamp:
        now = datetime.datetime.now(pytz.utc)
        ts = now - datetime.timedelta(
            hours=settings.LOG_ENTRIES_POLL_PAST_HOURS
        )
    else:
        ts = datetime.datetime.strptime(
            polling_timestamp, "%Y-%m-%d %H:%M:%S.%f%z"
        )

    params = {"since": str(ts)}
    processing_timestamp = db.get_now()
    try:
        log_entries = list(
            pagerduty.iter_all(settings.LOG_ENTRIES_ENDPOINT, params=params)
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
                logger.info(msg.format(log_entry["id"]))
                continue
            handle_log_entry(log_entry)

    # anyway put last timestamp the the db at the end of last issues polling
    utils.update_polling_timestamp(processing_timestamp)

    return result
