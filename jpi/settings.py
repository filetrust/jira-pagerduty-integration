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

# PagerDuty settings

PAGERDUTY_USER_NAME = os.environ["PAGERDUTY_USER_NAME"]

# Logging settings

LOGGING_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
