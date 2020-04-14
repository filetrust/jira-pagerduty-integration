import json
import requests
from requests.auth import HTTPBasicAuth
import urllib.parse

from jpi import settings


session = requests.Session()
session.auth = HTTPBasicAuth(settings.JIRA_USER_EMAIL, settings.JIRA_API_TOKEN)
session.headers = {
    "Accept": "application/json", "Content-Type": "application/json"
}


def jira_get_request(uri):
    response = session.get(f"{settings.JIRA_API_URL}{uri}")
    if not response.ok:
        if response.status_code in (400,):
            # Raise an exception this way in order to provide more
            # details located in `response.text`.
            raise Exception(response.text)
        else:
            response.raise_for_status()
    return response.json()


def jira_post_request(uri, data):
    response = session.post(f"{settings.JIRA_API_URL}{uri}", json=data)
    if not response.ok:
        if response.status_code in (400,):
            raise Exception(response.text)
        else:
            response.raise_for_status()
    if response.text:
        return response.json()


def text2doc(text):
    return {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "paragraph",
          "content": [
            {
              "text": text,
              "type": "text"
            }
          ]
        }
      ]
    }


def create_project(key, name):
    template_key = "com.pyxis.greenhopper.jira:gh-simplified-kanban-classic"
    data = {
        "name": name,
        "projectTypeKey": "software",
        "projectTemplateKey": template_key,
        "key": key.upper(),
        "leadAccountId": myself()["accountId"],
    }
    jira_post_request('/project', data)


def get_project(project_key):
    return jira_get_request(f'/project/{project_key}')


def server_info():
    return jira_get_request('/serverInfo')


def myself():
    return jira_get_request('/myself')


def get_issue(issue_key):
    return jira_get_request(f'/issue/{issue_key}')


def create_issue(fields):
    if 'description' in fields:
        fields['description'] = text2doc(fields['description'])
    return jira_post_request('/issue', {'fields': fields})


def get_issue_transitions(issue_key):
    resp = jira_get_request(f'/issue/{issue_key}/transitions')
    return resp['transitions']


def transition_issue(issue_key, transition_id):
    data = {
        'transition': transition_id,
    }
    return jira_post_request(f'/issue/{issue_key}/transitions', data)


def mark_issue_as_done(issue_key):
    done_transition_ids = [
        t["id"] for t in get_issue_transitions(issue_key)
        if t["name"] == "Done"
    ]
    transition_issue(issue_key, done_transition_ids[0])


def create_issue_link(issue_link_type_name, inward, outward):
    data = {
        "type": {
            "name": issue_link_type_name,
        },
        "inwardIssue": {
            "key": inward,
        },
        "outwardIssue": {
            "key": outward,
        },
    }
    return jira_post_request('/issueLink', data)


def get_fields():
    return jira_get_request('/field')


def search_issues(jql):
    jql = urllib.parse.quote(jql)
    resp = jira_get_request(
        f'/search?jql={jql}&startAt=0&validateQuery=True&maxResults=50')
    return resp


def create_issue_link_type(name, outward, inward):
    data = {"name": name, "outward": outward, "inward": inward}
    return jira_post_request('/issueLinkType', data)


def get_issue_link_types():
    return jira_get_request('/issueLinkType')['issueLinkTypes']


def create_issue_type(name, description="", issue_type_type="standard"):
    data = {"name": name, "description": description, "type": issue_type_type}
    return jira_post_request('/issuetype', data)


def get_issue_types():
    return jira_get_request('/issuetype')

