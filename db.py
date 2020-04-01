import os

import boto3
from boto3.dynamodb.conditions import Key

INCIDENTS_TABLE = os.environ['INCIDENTS_TABLE']
CRON_TABLE = os.environ['CRON_TABLE']
IS_OFFLINE = os.environ.get('IS_OFFLINE')

if IS_OFFLINE:
    resource = boto3.resource(
        'dynamodb',
        region_name='localhost',
        endpoint_url='http://localhost:8002'
    )
else:
    resource = boto3.resource('dynamodb')


def put_incident_issue_relation(incident_id, issue_key):
    incidents = resource.Table(INCIDENTS_TABLE)
    return incidents.put_item(
        Item={
            'incidentId': incident_id,
            'issueKey': issue_key,
        }
    )


def get_issue_key_by_incident_id(incident_id):
    incidents = resource.Table(INCIDENTS_TABLE)
    response = incidents.query(
        IndexName='incidentId',
        KeyConditionExpression=Key('incidentId').eq(incident_id)
    )
    if response.get('Count', 0) > 0:
        return response.get('Items')[0].get('issueKey')


def get_incident_id_by_issue_key(issue_key):
    incidents = resource.Table(INCIDENTS_TABLE)
    response = incidents.query(
        IndexName='issueKey',
        KeyConditionExpression=Key('issueKey').eq(issue_key)
    )
    if response.get('Count', 0) > 0:
        return response.get('Items')[0].get('incidentId')


def delete_relation_by_incident_id(incident_id):
    incidents = resource.Table(INCIDENTS_TABLE)
    response = incidents.query(
        IndexName='incidentId',
        KeyConditionExpression=Key('incidentId').eq(incident_id)
    )
    items = response.get('Items')
    if items:
        incidents.delete_item(
            Key=items[0]
        )


def delete_relation_by_issue_key(issue_key):
    incidents = resource.Table(INCIDENTS_TABLE)
    response = incidents.query(
        IndexName='issueKey',
        KeyConditionExpression=Key('issueKey').eq(issue_key)
    )
    items = response.get('Items')
    if items:
        incidents.delete_item(
            Key=items[0]
        )


def put_cron_incident(incident_id, priority):
    cron = resource.Table(CRON_TABLE)
    return cron.put_item(
        Item={
            'incidentId': incident_id,
            'priority': priority
        }
    )


def get_priority_by_incident_id(incident_id):
    cron = resource.Table(CRON_TABLE)
    response = cron.query(
        KeyConditionExpression=Key('incidentId').eq(incident_id)
    )
    items = response.get('Items')
    if items:
        return items[0].get('priority')


def delete_cron_entry_by_incident_id(incident_id):
    cron = resource.Table(CRON_TABLE)
    response = cron.query(
        KeyConditionExpression=Key('incidentId').eq(incident_id)
    )
    items = response.get('Items')
    if items:
        cron.delete_item(
            Key={'incidentId': incident_id}
        )
