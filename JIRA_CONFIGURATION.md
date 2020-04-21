# Jira configuration

In order to configure Jira Cloud (for testing and development
purposes) execute the steps described below. The commands create
projects, issue types etc. The commands create the same projects as we
have on [official Jira Cloud](http://glasswall.atlassian.net/). So
basically the commands were created in order to mimic the official
Jira with its projects (such as `Incident`, `Person`), issue types
(again `Incident`, `Person`) and so on.

## Step 1

Create **issue types** and **projects**

```
dotenv run python -m jpi.tools.jira_configuration --step 1
```

## Step 2

To check Project creation open in browser
[Projects - Jira](https://glasswall-dev.atlassian.net/secure/BrowseProjects.jspa)

Navigate to 
[Issue Type Schemes - Jira](https://glasswall-dev.atlassian.net/secure/admin/ManageIssueTypeSchemes!default.jspa)
Issue Type Schemes at the beginning
![Issue Types](docs/images/IssueTypes-Initial.png)

Open every Issue Type Scheme
![Edit Issue Schem](docs/images/IssueType-StartEdit.png)

Manually edit the Scheme and leave only one Issue Type per correspondent
Project. Click Save button.
![Edit Issue Schem](docs/images/IssueType-Edited.png)

The final screen should looks like 
![Issue Types - Final screen](docs/images/IssueTypes-Final.png)

## Step 3

Run script to finalize JIRA configuration.

```
dotenv run python -m jpi.tools.jira_configuration --step 2
```
