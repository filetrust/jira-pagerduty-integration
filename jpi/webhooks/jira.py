import logging

from jpi import db, settings, utils


logger = logging.getLogger(__name__)


def webhook_handler(event):
    """
    A webhook handler that should handle the events triggered by
    Jira webhook.
    """
    changelog = event.get("changelog", {})
    changes = changelog.get("items", [{}])

    has_done = False
    for item in changes:
        if item.get("fieldId") == "status" and item.get("toString") == "Done":
            has_done = True
            break
    issue_key = None
    if has_done:
        issue_key = event.get("issue", {}).get("key")
    if issue_key is not None:
        incident_id = db.get_incident_id_by_issue_key(issue_key)
        if incident_id:
            pagerduty = utils.get_pagerduty()
            try:
                pagerduty.rput(
                    settings.INCIDENT_ENDPOINT,
                    json=[{
                        "id": incident_id,
                        "type": "incident_reference",
                        "status": settings.STATUS_RESOLVED,
                    }],
                )
                utils.resolve_incident(incident_id)
            except Exception:
                msg = (
                    f"[{incident_id}] Exception occurred during updating of "
                    f"a PagerDuty incident"
                )
                logger.exception(msg)
