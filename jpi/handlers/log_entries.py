import datetime
import logging
import os
import re

from jira.exceptions import JIRAError
from pdpyras import PDClientError
import pytz

from jpi import db, utils

LOG_ENTRIES_ENDPOINT = "/log_entries"
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TIMELINE_PROJECT_KEY = os.environ["TIMELINE_PROJECT_KEY"]
ISSUE_KEY_FIELD_NAME = "issueKey"
INCIDENT_NUMBER_FIELD_NAME = "incident_number"


def handle_priority_change_log_entry(log_entry):
    pattern = re.compile(r'Priority changed from "P\d" to "P1"')
    if pattern.match(log_entry["summary"]):
        logger.info("[{}] {}".format(log_entry["id"], log_entry["summary"]))
        agent = log_entry["agent"]
        incident_manager = utils.get_incident_manager(agent["summary"])
        incident = log_entry["incident"]
        issue_key = db.get_issue_key_by_incident_id(incident["id"])
        incident_fields = {}
        incident_fields["priority"] = log_entry["channel"]["new_priority"][
            "summary"
        ]
        if not issue_key:
            # Issue doesn't exist, let's create it.
            issue = utils.create_jira_incident(
                incident["summary"], incident_manager=incident_manager
            )
            incident_fields[ISSUE_KEY_FIELD_NAME] = issue.key
        db.put_incident(incident["id"], incident_fields)


def handle_log_entry(log_entry):
    jira = utils.get_jira()
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
            jira.issue(issue_key)
        except JIRAError:
            msg = "[{}] Error occurred while retrieving Jira issue"
            logger.exception(msg.format(log_entry["id"]))
            return

        issue_dict = {
            "project": {"key": os.environ["TIMELINE_PROJECT_KEY"]},
            "summary": log_entry["summary"],
            "issuetype": {"name": "Bug"},
        }
        try:
            timeline_issue = jira.create_issue(fields=issue_dict)
            logger.info(
                'Timeline issue "{}" successfully created'.format(
                    timeline_issue.key
                )
            )
            utils.link_issue(timeline_issue.key, issue_key, "has timeline")
        except JIRAError:
            msg = "[{}] Error creating timeline link to Jira issue {}"
            logger.exception(msg.format(issue_key))
            return
        db.put_log_entry(log_entry["id"])
    else:
        logger.info("[{}] Issue key not found".format(log_entry["id"]))


def handler(event, context):
    result = {"ok": True}
    pagerduty = utils.get_pagerduty()
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
                logger.info(msg.format(log_entry["id"]))
                continue
            handle_log_entry(log_entry)

    # anyway put last timestamp the the db at the end of last issues polling
    db.update_polling_timestamp(processing_timestamp)

    return result
