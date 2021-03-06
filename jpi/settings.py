import os


PROJECT_PATH = os.path.abspath(os.path.dirname(__name__))
IS_OFFLINE = os.environ.get("IS_OFFLINE")
QUESTIONS_FILE = os.environ["QUESTIONS_FILE"]

# Jira settings

JIRA_USER_EMAIL = os.environ["JIRA_USER_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]
JIRA_SERVER_URL = os.environ["JIRA_SERVER_URL"]
JIRA_API_URL = f"{JIRA_SERVER_URL}/rest/api/3"

QUESTION_ISSUE_TYPE_NAME = "Question"
INCIDENT_MANAGER_ISSUE_TYPE_NAME = "Incident Manager"
TIMELINE_ISSUE_TYPE_NAME = "Timeline"
STAKEHOLDER_ISSUE_TYPE_NAME = "Stakeholder"

GLASSWALL_JIRA_PROJECT_KEYS = [
    "INCIDENT",
    "PERSON",
    "TIMELINE",
    "QUESTION",
]

INCIDENT_PROJECT_KEY = os.environ["INCIDENT_PROJECT_KEY"]
PERSON_PROJECT_KEY = os.environ["PERSON_PROJECT_KEY"]
TIMELINE_PROJECT_KEY = os.environ["TIMELINE_PROJECT_KEY"]
QUESTION_PROJECT_KEY = os.environ["QUESTION_PROJECT_KEY"]

JIRA_ISSUE_STAKEHOLDERS = os.environ.get("JIRA_ISSUE_STAKEHOLDERS", "")

JIRA_SEVERITY_FIELD_NAME = "Severity"
JIRA_INCIDENT_SEVERITY = "SEV-0"

# PagerDuty settings

PAGERDUTY_API_TOKEN = os.environ["PAGERDUTY_API_TOKEN"]
PAGERDUTY_USER_NAME = os.environ.get("PAGERDUTY_USER_NAME", "")
PAGERDUTY_USER_EMAIL = os.environ["PAGERDUTY_USER_EMAIL"]

LOG_ENTRIES_ENDPOINT = "/log_entries"
INCIDENT_ENDPOINT = "incidents"
STATUS_RESOLVED = "resolved"
LOG_ENTRIES_POLL_PAST_HOURS = int(
    os.environ.get("LOG_ENTRIES_POLL_PAST_HOURS", 1)
)
P1_PRIORITY_NAME = "P1"

# Logging settings

LOGGING_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"

# Database settings

DATABASE_ENDPOINT_URL = "http://localhost:8002"

INCIDENTS_TABLE = os.environ.get("INCIDENTS_TABLE", "incidents-dev")
LOG_ENTRIES_TABLE = os.environ.get("LOG_ENTRIES_TABLE", "log-entries-dev")
CONFIG_TABLE = os.environ.get("CONFIG_TABLE", "config-dev")

CONFIG_PARAMETER_FIELD_NAME = "parameterName"
CONFIG_VALUE_FIELD_NAME = "value"
ISSUE_KEY_FIELD_NAME = "issueKey"
INCIDENT_ID_FIELD_NAME = "incidentId"
LOG_ENTRY_ID_FIELD_NAME = "logEntryId"
LAST_POLLING_TIMESTAMP_PARAM = "LastPollingTimestamp"
RESOLVED_FIELD_NAME = "resolved"
INCIDENT_NUMBER_FIELD_NAME = "incident_number"
