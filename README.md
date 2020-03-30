# Project installation and configuration

Clone the project:

```
git clone git@github.com:filetrust/gw-proxy-serverless.git
```

and cd to the project directory:

```
cd pagerduty-jira-synchronization
```

##Make and activate a virtual environment:

```
python -m venv env
source env/bin/activate
```

## Add python frameworks

```pip instal -r requirements.txt```

## Install `serverless`:

```
npm install -g serverless
```

and other dependencies:

```
npm install
```

## Local DynamoDB

For local development download local-based DynamoDB package from 
[AWS DynamoDB](https://docs.aws.amazon.com/dynamodb/index.html) service 

```sls dynamodb install```

# Configure Jira

Sign up and create a project.

Go to [API tokens](https://id.atlassian.com/manage/api-tokens) and
create API token.

Copy `.env.example` to `.env` and edit it. Put your email to
`JIRA_USER_EMAIL`, put the API token to `JIRA_API_TOKEN`, put your
atlassian root URL (e.g. https://username.atlassian.net) to
`JIRA_SERVER_URL`. Put the key of your project to `JIRA_PROJECT_KEY`
(you can find the key in the list of the existing projects).


# AWS configuration

Be sure you have a configured account on Amazon - AWS.

If not done before, register new account on [AWS](https://aws.amazon.com/). 
Good practice if you will use not root account for deploying the application
After all required steps for creating finished, you need to create new user 
in [AWS Console](https://console.aws.amazon.com/iam/home#/users). 
Let name it **gwuser**. 

Add admin permissions to the **gwuser** and then login to the AWS Console 
under **gwuser** credentials [AWS Credential page](https://console.aws.amazon.com/iam/home?#/security_credentials).
Generate new access key. Download generated file AccessKeys.csv

Get back to the termanal and install _awscli_ utility via

```pip instal awscli ```

After that you can configure aws credential on you machine

```aws configure```

The screen should looks like

```
AWS Access Key ID [None]: AKIAI44QH8DHBEXAMPLE
AWS Secret Access Key [None]: je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: text
```


# Deploy serverless application

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

Append `/pagerduty-webhook` to the endpoint and use it as an URL for a
PagerDuty webhook.

# Configure PagerDuty webhook

Go to [Extensions](https://atykhonov.pagerduty.com/extensions) page,
click on `New Extension`, select `Generic V2 Webhook`, put into `Name`
some name (e.g. `pjsync`), select an existing PagerDuty service
(create it if it doesn't exist) and input the PagerDuty webhook URL
into `URL` field. Click `Save`.

After this the serverless application should be executed each time
when a new incident is created.



#Local Development

For agile development good idea to setup development local-based environment,
which complete resembling the production, based on serverless/AWS stack.

## Run database instance

Run the database instance locally on http://localhost:8002

```sls dynamodb start```

For checking the db is up and running open in browser http://localhost:8002/shell/ page.


## Run application local

The command runs flask-base http server on 5000 port locally on the development machine.

```sls wsgi serve```


## Expose local server to public URL


Download [Ngrok](https://ngrok.com), the brilliant solution for that.


```ngrok http 5000```


If you register your instance on the **Ngrok** site, you may get following screen.

```
Session Status                online
Account                       Upwork Developer (Plan: Free)
Version                       2.3.35
Region                        United States (us)
Web Interface                 http://127.0.0.1:4040
Forwarding                    http://9d0af513.ngrok.io -> http://localhost:5000
Forwarding                    https://9d0af513.ngrok.io -> http://localhost:5000

Replace webhook URL on the PagerDuty site with generated link https://9d0af513.ngrok.io
and now PagerDuty instance will trigger your local environment, rather then deployed
to the Amazon Lambda service.
```
 