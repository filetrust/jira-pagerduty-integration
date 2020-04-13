import logging
import sys

from jira.exceptions import JIRAError
from requests.auth import HTTPBasicAuth

from jpi import settings, utils
from .jiraconfiguration import create_project, create_issue, create_issue_type

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format=settings.LOGGING_FORMAT
)
[
    logging.getLogger(p).setLevel(logging.ERROR)
    for p in ["faker.factory", "urllib3"]
]
logger = logging.getLogger()
jira = utils.get_jira()
auth = HTTPBasicAuth(settings.JIRA_USER_EMAIL, settings.JIRA_API_TOKEN)

headers = {"Accept": "application/json", "Content-Type": "application/json"}

if __name__ == "__main__":
    issue_types_to_create = []
    for project_key in settings.GLASSWALL_JIRA_PROJECT_KEYS:
        issue_types_to_create.append(project_key.title())
    issue_types_not_to_create = [
        item_type.name for item_type in jira.issue_types()
        if (item_type.name in issue_types_to_create)
    ]
    for project_key in settings.GLASSWALL_JIRA_PROJECT_KEYS:
        project = create_project(project_key, project_key.title() + 's')

    for project_key in issue_types_to_create:
        if project_key not in issue_types_not_to_create:
            issue_type_key = project_key.title()
            try:
                create_issue_type(
                    issue_type_key,
                    description=f"Corresponding to Glasswall {issue_type_key}"
                )
            except JIRAError:
                msg = f"Error creating of {issue_type_key} issue type for " \
                      f"{project_key} project"
                logger.exception(msg)
            else:
                logger.info(f"{issue_type_key} issue type already created ")
    else:
        logger.info("All issue types already created")
