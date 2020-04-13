import logging

from jira.exceptions import JIRAError

from jpi import db, settings, utils


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
                issue_key = issue.key
                incident_fields[settings.ISSUE_KEY_FIELD_NAME] = issue_key
                db.put_incident(incident_id, incident_fields)
    else:
        db.put_incident(incident_id, incident_fields)

    return issue_key


def handle_resolved_incident(message):
    incident = message.get("incident")
    incident_id = incident["id"]
    issue_key = db.get_issue_key_by_incident_id(incident_id)
    if issue_key:
        jira = utils.get_jira()
        issue = jira.issue(issue_key)
        done_transition_ids = [
            t["id"] for t in jira.transitions(issue) if t["name"] == "Done"
        ]
        if done_transition_ids:
            try:
                jira.transition_issue(issue, done_transition_ids[0])
                utils.resolve_incident(incident_id)
            except JIRAError:
                logger.exception("Error occurred during resolving Jira issue")


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
