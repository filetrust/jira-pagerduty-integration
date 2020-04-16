# Project installation and configuration

Clone the project:

```
git clone git@github.com:filetrust/jira-pagerduty-integration.git
```

and cd to the project directory:

```
cd jira-pagerduty-integration
```

## Make and activate a virtual environment:

```
pipenv --python 3.7
source $(pipenv --venv)/bin/activate
```

## Install python dependencies

```
pipenv install --dev
```

## Install `serverless`:

### Install `npm`

If you don't have `npm` installed, you can install it by means of the
following command:

```
nodeenv -p
```

Now install `serverless`:

```
npm install -g serverless
```

and other dependencies:

```
npm install
```

## PagerDuty and Jira API tokens

### PagerDuty API tokens

Go to [API Access Keys](https://glasswall-dev.pagerduty.com/api_keys) and
create a new API key.

### Jira API tokens

Go to [API tokens](https://id.atlassian.com/manage/api-tokens) and
create an API token.

## Create a configuration file

Copy `.env.example` to `.env` and edit it. Put your email to
`JIRA_USER_EMAIL` and `PAGERDUTY_USER_EMAIL`, put the API tokens to
`JIRA_API_TOKEN` and `PAGERDUTY_API_TOKEN`, put your atlassian root
URL (e.g. https://glasswall-dev.atlassian.net) to `JIRA_SERVER_URL`.

Put the full name of PagerDuty user into `PAGERDUTY_USER_NAME`
variable (this is for the dev and test environments only, i.e. no
needs to have the variable configured on production
environment). During execution of `jpi.tools.jira_configuration` (see
below) the full name is used to create a Jira issue in `PERSON`
project. When a Jira issue is created by the integration, a Jira issue
(in `PERSON` project) is searched by PagerDuty assignee. If the issue
is found then it is linked to the newly created issue using `Incident
Manager` link type.

## Jira configuration

In order to generate fake Jira projects and issues (for testing and
development purposes) see [Jira configuration](JIRA_CONFIGURATION.md).

## PagerDuty configuration

Go to [Incident Priority Settings
](https://glasswall-dev.pagerduty.com/account/incident_priorities) and
make sure that Incident Priority Levels are enabled.

## AWS configuration

Configure `awscli` on your machine:

```
aws configure
```

Then do the remaining AWS configurations using the following command:

```
./jpi/tools/aws_configuration.sh
```

The command creates `jpi-cfn-role` role and outputs its ARN. Put the
ARN into `CFN_ROLE_ARN` variable (`.env` file).

## Install and run local DynamoDB

Install DynamoDB by means of the following command:

```
sls dynamodb install
```

and start it

```
sls dynamodb start
```

## Serve the WSGI application locally

Execute the following command in order to start the local server:

```
sls wsgi serve
```

## Expose your local web server.

Download, install and execute [ngrok](https://ngrok.com):

```
ngrok http 5000
```

Use the https URL to create the URLs for PagerDuty and Jira
webhooks (read below).

## Configure PagerDuty webhook

Go to [Extensions](https://glasswall-dev.pagerduty.com/extensions) and
create a New Extension with `Extension Type` equals to `Generic V2
Webhook`, `Name` equals to `jpi`, `Service` equals to any available
service that you created before and URL equals to
`<ngrok-url>/pagerduty-webhook`.

## Configure Jira webhook

Go to [System
WebHooks](https://glasswall-dev.atlassian.net/plugins/servlet/webhooks)
and create a webhook with any convenient name and with URL equals to
`<ngrok-url>/jira-webhook`.

## Test the configuration

Go to PagerDuty and create an incident with any `Impacted Service`,
with any convenient `Title` and with `Incident Priority` equals to
`P1`. Go to Jira, open `Incidents` project and check the issues. You
should see the newly created issue with the same title you just
inputed.

## Scheduled functions

The functionality of the project depends on `log_entries` function
that should be executed periodically. On a dev environment the
function is not executed periodically so it should be manually
trigerred when you need it to be executed, e.g.:

```
IS_OFFLINE=True sls invoke local -f log_entries
```

Create an incident with `Incident Priority` equals to `P2`. An
incident created with priority other than `P1` shouldn't be
automatically created in Jira. But, accordingly to the requirements,
when priority is changed to `P1` an issue should be created in
Jira. Change `Incident Priority` to `P1` of the recently created
incident and execute the following command:

```
IS_OFFLINE=True sls invoke local -f log_entries
```

Open Jira and check that the issue was created.

# Deploy serverless application to dev environment (AWS)

In order to deploy the application execute the following command:

```
sls deploy
```

The command should output an endpoint URL, for instance:

```
[...]
endpoints:
  ANY - https://oqzgxd0euf.execute-api.us-east-1.amazonaws.com/dev
  ANY - https://oqzgxd0euf.execute-api.us-east-1.amazonaws.com/dev/{proxy+}
[...]

```

Use the endpoint URL to configure the webhooks in PagerDuty and Jira.

In order to execute the scheduled functions (e.g. `log_entries`) use
the following command:

```
sls invoke local -f log_entries
```

# Deploy serverless application to qa environment

In order to deploy the application to qa environment execute the
following commands:

```
sls login
sls deploy --env qa
```

The scheduled functions should be executed automatically (no needs to
execute them manually).
