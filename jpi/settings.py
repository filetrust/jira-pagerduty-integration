import os


PROJECT_PATH = os.path.abspath(os.path.dirname(__name__))

# Jira settings

JIRA_USER_EMAIL = os.environ["JIRA_USER_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]
JIRA_SERVER_URL = os.environ["JIRA_SERVER_URL"]
JIRA_API_URL = f"{JIRA_SERVER_URL}/rest/api/3"

QUESTION_ISSUE_TYPE_NAME = "Question"
INCIDENT_MANAGER_ISSUE_TYPE_NAME = "Incident Manager"
TIMELINE_ISSUE_TYPE_NAME = "Timeline"
STAKEHOLDER_ISSUE_TYPE_NAME = "Stakeholder"

INCIDENT_PROJECT_KEY = os.environ["INCIDENT_PROJECT_KEY"]
PERSON_PROJECT_KEY = os.environ["PERSON_PROJECT_KEY"]
TIMELINE_PROJECT_KEY = os.environ["TIMELINE_PROJECT_KEY"]
QUESTION_PROJECT_KEY = os.environ["QUESTION_PROJECT_KEY"]

JIRA_ISSUE_STAKEHOLDERS = os.environ.get("JIRA_ISSUE_STAKEHOLDERS", "")

JIRA_INCIDENT_SEVERITY = "SEV-0"

# PagerDuty settings

PAGERDUTY_USER_NAME = os.environ["PAGERDUTY_USER_NAME"]
LOG_ENTRIES_ENDPOINT = "/log_entries"
LOG_ENTRIES_POLL_PAST_HOURS = \
    int(os.environ.get("LOG_ENTRIES_POLL_PAST_HOURS", 1))

# Logging settings

LOGGING_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"

# Database settings

ISSUE_KEY_FIELD_NAME = "issueKey"
