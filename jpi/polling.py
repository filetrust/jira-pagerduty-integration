import datetime
import logging
import os

from jira.exceptions import JIRAError

from jpi import db
from jpi import utils


LOG_ENTRIES_ENDPOINT = "/log_entries"
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TIMELINE_PROJECT_KEY = os.environ["TIMELINE_PROJECT_KEY"]


def log_entries(event, context):
    pagerduty = utils.get_pagerduty()
    jira = utils.get_jira()
    poll_past_hours = int(os.environ.get("LOG_ENTRIES_POLL_PAST_HOURS"))
    now = datetime.datetime.now()
    params = {"since": now - datetime.timedelta(hours=poll_past_hours)}
    log_entries = list(pagerduty.iter_all(LOG_ENTRIES_ENDPOINT, params=params))
    logger.info("{} log entries found".format(len(log_entries)))
    for log_entry in log_entries:
        if db.get_log_entry_by_id(log_entry["id"]):
            msg = "[{}] Existing log entry found. Skipping..."
            msg = msg.format(log_entry["id"])
            logger.info(msg)
            continue
        if log_entry["type"] == "status_update_log_entry":
            logger.info("[{}] New status update found".format(log_entry["id"]))
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
                else:
                    issue_dict = {
                        "project": {"key": os.environ["TIMELINE_PROJECT_KEY"]},
                        "summary": log_entry["message"],
                        "issuetype": {"name": "Bug"},
                    }
                    timeline_issue = jira.create_issue(fields=issue_dict)
                    logger.info(
                        'Timeline issue "{}" successfully created'.format(
                            timeline_issue.key
                        )
                    )
                    utils.link_issue(
                        timeline_issue.key, issue_key, "has timeline"
                    )
            else:
                logger.info("[{}] Issue key not found".format(log_entry["id"]))
        db.put_log_entry(log_entry["id"])
    return {
        "ok": True,
    }
