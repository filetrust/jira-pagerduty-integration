import logging
from requests.exceptions import HTTPError

from jpi import db, settings, utils
from jpi.api import jira


logger = logging.getLogger()


def handle_triggered_incident(message):
    incident = message.get("incident", {})
    incident_id = incident["id"]
    issue_key = None
    priority = incident.get("priority")
    high_priority = False
    incident_fields = {}
    if priority:
        priority_name = priority.get("name")
        if priority_name:
            incident_fields["priority"] = priority_name
            high_priority = priority_name == settings.P1_PRIORITY_NAME
    incident_fields[settings.INCIDENT_NUMBER_FIELD_NAME] = incident.get(
        settings.INCIDENT_NUMBER_FIELD_NAME
    )

    if high_priority:
        db_issue_key = db.get_issue_key_by_incident_id(incident_id)
        if not db_issue_key:
            entries = message.get("log_entries", [])
            for entry in entries:
                incident_manager = utils.get_incident_manager(
                    entries[0]["agent"]["summary"]
                )
                issue = utils.create_jira_incident(
                    entry["channel"]["summary"],
                    entry["channel"]["details"],
                    incident_manager=incident_manager,
                )
                incident_fields[settings.ISSUE_KEY_FIELD_NAME] = issue['key']
                db.put_incident(incident_id, incident_fields)
    else:
        db.put_incident(incident_id, incident_fields)


def handle_resolved_incident(message):
    incident = message.get("incident")
    incident_id = incident["id"]
    issue_key = db.get_issue_key_by_incident_id(incident_id)
    if issue_key:
        try:
            jira.get_issue(issue_key)
        except HTTPError:
            logger.exception("Error occurred when getting Jira issue")
        try:
            jira.mark_issue_as_done(issue_key)
            utils.resolve_incident(incident_id)
        except HTTPError:
            logger.exception("Error occurred while resolving Jira issue")


def webhook_handler(event):
    """
    A webhook handler that should handle the events triggered by
    PagerDuty webhook.
    """
    messages = event.get("messages", [])
    for message in messages:
        if message.get("event") == "incident.trigger":
            handle_triggered_incident(message)
        elif message.get("event") == "incident.resolve":
            handle_resolved_incident(message)
