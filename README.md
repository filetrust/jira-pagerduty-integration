# Jira Cloud and PagerDuty integration

## Requirements

- Python 3.7
- Pipenv
- Docker
- Node.js and npm (can be installed by means of `nodeenv`, see below)
- AWS account
- Jira Cloud account
- PagerDuty account
- account on [Serverless](https://serverless.com) and access to
  `glasswall` organization (optional);
- ngrok (optional, it is useful for dev purposes only)

## Project overview

The integration allows to automatically copy to Jira Cloud the changes
made by a user on PagerDuty and wise versa. For instance, a Jira issue
is created when a user creates an incident (with P1 priority) on
PagerDuty.

### Generic architecture notes

In order to handle a change made by a user on either PagerDuty or on
Jira Cloud the webhooks are employed. For sorry not all changes are
possible to handle by means of the webhooks. If Jira allows an admin
to create a webhook for almost all events that might occur on Jira
Cloud, in contrast, PagerDuty has limited set of available
webhooks. For instance, there is a webhook for the events when an
incident was created, but there is no a webhook for tracking when an
incident was updated (see the [Developer
Documentation](https://v2.developer.pagerduty.com/docs/webhooks-v2-overview)
for more details). As a workaround the changes are periodically
fetched from PagerDuty REST API by means of the scheduled function
(see `jpi.handlers.log_entries.handler`). All the events that happen
to an Incident are exposed as Log Entries that are available via
`/log_entries` API endpoint (see [REST API
Reference](https://developer.pagerduty.com/api-reference/reference/REST/openapiv3.json/paths/~1log_entries/get)
for more details). By means of the log entries the changes (such as
priority change) are tracked by the integration and are copied to Jira
Cloud. The scheduled function is executed periodically (interval is
defined in `PAGERDUTY_POLL_INTERVAL` environment variable). It is
executed automatically only in the deployments made to an account on
[Serverless](https://serverless.com). On any other environments the
scheduled function should be manually executed.

### Deployment notes

This `README.md` first of all is devoted to developers and for
development purposes. Thus here a lot of information on how to create
a local development environment from the scratch. The information
highlights all details of the project, its configuration etc. If you
need to just deploy the integration please refer to [Deployment to
serverless dev
environment](#deployment-to-serverless-dev-environment).

## Project installation and configuration

Clone the project:

```
git clone git@github.com:filetrust/jira-pagerduty-integration.git
```

and cd to the project directory:

```
cd jira-pagerduty-integration
```

### Make and activate a virtual environment:

```
pipenv --python 3.7
source $(pipenv --venv)/bin/activate
```

### Install python dependencies

```
pipenv install --dev
```

### Install Node.js dependencies

#### Install `npm`

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

### PagerDuty and Jira API tokens

#### PagerDuty API tokens

Go to [API Access Keys](https://username.pagerduty.com/api_keys) and
create a new API key.

#### Jira API tokens

Go to [API tokens](https://id.atlassian.com/manage/api-tokens) and
create an API token.

### Create a configuration file

Copy `.env.example` to `.env` and edit it. Put your email to
`JIRA_USER_EMAIL` and `PAGERDUTY_USER_EMAIL`, put the API tokens to
`JIRA_API_TOKEN` and `PAGERDUTY_API_TOKEN`, put your atlassian root
URL (e.g. https://username.atlassian.net) to `JIRA_SERVER_URL`.

Put the full name of PagerDuty user into `PAGERDUTY_USER_NAME`
variable (this is for the dev and test environments only, i.e. no
needs to have the variable configured on production
environment). During execution of `jpi.tools.jira_configuration` (see
below) the full name is used to create a Jira issue in `PERSON`
project. When a Jira issue is created by the integration, a Jira issue
(in `PERSON` project) is searched by PagerDuty assignee. If the issue
is found then it is linked to the newly created issue using `Incident
Manager` link type.

### Jira configuration

In order to configure Jira Cloud (for testing and development
purposes) see [Jira configuration](JIRA_CONFIGURATION.md).

### PagerDuty configuration

Go to [Incident Priority Settings
](https://username.pagerduty.com/account/incident_priorities) and
make sure that Incident Priority Levels are enabled.

### AWS configuration

Configure `awscli` on your machine:

```
aws configure
```

Then do the remaining AWS configurations using the following command:

```
dotenv run python -m jpi.tools.aws_configuration
```

The command creates `jpi-cfn-role` role and outputs its ARN. Put the
ARN into `CFN_ROLE_ARN` variable (`.env` file).

### Install and run local DynamoDB

Install DynamoDB by means of the following command:

```
sls dynamodb install
```

and start it

```
sls dynamodb start
```

### Serve the WSGI application locally

Execute the following command in order to start the local server:

```
sls wsgi serve
```

### Expose your local web server.

Download, install and execute [ngrok](https://ngrok.com):

```
ngrok http 5000
```

Use the https URL to create the URLs for PagerDuty and Jira
webhooks (read below).

### Configure PagerDuty webhook

Go to [Extensions](https://username.pagerduty.com/extensions) and
create a New Extension with `Extension Type` equals to `Generic V2
Webhook`, `Name` equals to `jpi`, `Service` equals to any available
service that you created before and URL equals to
`<endpoint-url>/pagerduty-webhook`.

### Configure Jira webhook

Go to [System
WebHooks](https://username.atlassian.net/plugins/servlet/webhooks)
and create a webhook with any convenient name and with URL equals to
`<endpoint-url>/jira-webhook`.

### Test the configuration

Go to PagerDuty and create an incident with any `Impacted Service`,
with any convenient `Title` and with `Incident Priority` equals to
`P1`. Go to Jira, open `Incidents` project and check the issues. You
should see the newly created issue with the same title you just
inputed.

### Scheduled functions

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

## Deployment to remote AWS dev environment

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

## Deployment to Serverless dev environment

1) [Clone the project](#project-installation-and-configuration),
install [python](#install-python-dependencies) and
[Node.js](#install-nodejs-dependencies) dependencies. Create `.env`
and change the settings in it;

2) Be sure that you have been invited to `glasswall` organization on
[Serverless](https://serverless.com); if not, please ask an owner
([Andrii Tykhonov](mailto:atykhonov+glasswall@gmail.com)) to invite
you.

3) [Create CFN Service Role](#aws-configuration) on AWS (the role
should be used for `CFN_ROLE_ARN` variable);

4) [Create API tokens](#pagerduty-and-jira-api-tokens) on PagerDuty
and Jira Cloud;

5) Log into Serverless by means of the command `sls login`;

6) Deploy the integration to glasswall organization on
[Serverless](https://serverless.com) by means of `sls deploy` command;

7) `sls deploy` should output the endpoints like this:

```
endpoints:
  ANY - https://io9tozfjve.execute-api.us-east-1.amazonaws.com/prod
  ANY - https://io9tozfjve.execute-api.us-east-1.amazonaws.com/prod/{proxy+}
```

8) Use the first endpoint to configure the webhooks on
[PagerDuty](#configure-pagerduty-webhook) and [Jira
Cloud](#configure-jira-webhook);

9) Configure [PagerDuty](#pagerduty-configuration) and [Jira
Cloud](#jira-configuration);

10) Create an issue on PagerDuty (with P1 priority) and check that it
is copied to Jira Cloud.

## Deployment to Serverless qa environment

Everything that you need in order to deploy to Serverless qa
environment is basically described in the [previous
section](#deployment-to-serverless-dev-environment). Instead of `.env`
please create `.env.qa` file with its own settings. Please make sure
that it contains `STAGE=qa`. And use the following command in order to
deploy the integration:

```
sls deploy --env qa
```

## Deployment to Serverless prod environment

Everything required for prod deployment is described in the [previous
sections](#deployment-to-serverless-dev-environment). Instead of
`.env` please create `.env.prod` file with its own settings. Please
make sure that it contains `STAGE=prod`. And use the following command
in order to deploy the integration:

```
sls deploy --env prod
```

Please note that the section contains information about PagerDuty and
Jira configuration. Please skip the configuration, you don't need to
configure them for prod environment (of course it is still required to
create the API tokens and the webhooks for both PagerDuty and Jira
Cloud).
