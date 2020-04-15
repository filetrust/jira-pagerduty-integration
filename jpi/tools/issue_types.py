from jpi import settings
from .jiraconfiguration import create_project, create_issue_type

if __name__ == "__main__":
    for project_key in settings.GLASSWALL_JIRA_PROJECT_KEYS:
        project = create_project(project_key, project_key.title() + 's')
        issue_type_key = project_key.title()
        create_issue_type(
            issue_type_key,
            description=f"Corresponding to Glasswall {issue_type_key}"
        )
