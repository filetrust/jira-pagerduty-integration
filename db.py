import os

import boto3
from boto3.dynamodb.conditions import Key

INCIDENTS_TABLE = os.environ['INCIDENTS_TABLE']
IS_OFFLINE = os.environ.get('IS_OFFLINE')

if IS_OFFLINE:
    resource = boto3.resource(
        'dynamodb',
        region_name='localhost',
        endpoint_url='http://localhost:8002'
    )
else:
    resource = boto3.resource('dynamodb')


def put_incident(incident_id, incident_fields=None):
    """

    """
    if incident_fields is None:
        incident_fields = {}
    incidents_table = resource.Table(INCIDENTS_TABLE)
    incident = get_incident_by_id(incident_id)
    if incident:
        item = {
            **incident,
            **incident_fields
        }
    else:
        item = {
            **{'incidentId': incident_id},
            **incident_fields
        }

    return incidents_table.put_item(
        Item=item
    )


def get_incident_by_id(incident_id, resolved=False):
    incidents = resource.Table(INCIDENTS_TABLE)
    response = incidents.query(
        KeyConditionExpression=Key('incidentId').eq(incident_id)
    )
    if response.get('Count', 0) > 0:
        incident = response.get('Items')[0]
        incident_resolved = incident.get('resolved', False)
        if not resolved or not incident_resolved:
            return incident


def get_issue_key_by_incident_id(incident_id):
    incident = get_incident_by_id(incident_id)
    if incident:
        incident.get('issueKey')


def get_incident_id_by_issue_key(issue_key):
    incidents = resource.Table(INCIDENTS_TABLE)
    response = incidents.scan(
        KeyConditionExpression=Key('issueKey').eq(issue_key)
    )
    if response.get('Count', 0) > 0:
        return response.get('Items')[0].get('incidentId')


def resolve_incident(incident_id):
    put_incident(incident_id, {'resolved': True})
