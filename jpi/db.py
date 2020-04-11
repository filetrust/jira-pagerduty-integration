from datetime import datetime
import os
import pytz

import boto3
from boto3.dynamodb.conditions import Attr, Key


INCIDENTS_TABLE = os.environ["INCIDENTS_TABLE"]
LOG_ENTRIES_TABLE = os.environ["LOG_ENTRIES_TABLE"]
CONFIG_TABLE = os.environ["CONFIG_TABLE"]
IS_OFFLINE = os.environ.get("IS_OFFLINE")

CREATED_FIELD_NAME = "created"
UPDATED_FIELD_NAME = "updated"
RESOLVED_FIELD_NAME = "resolved"
CONFIG_PARAMETER_FIELD_NAME = "parameterName"
CONFIG_VALUE_FIELD_NAME = "value"

LAST_POLLING_TIMESTAMP_PARAM='LastPollingTimestamp'

if IS_OFFLINE:
    resource = boto3.resource(
        "dynamodb",
        region_name="localhost",
        endpoint_url="http://localhost:8002",
    )
else:
    resource = boto3.resource("dynamodb")


def get_now():
    now = datetime.now(pytz.utc)
    return str(now)


def put_incident(incident_id, incident_fields=None):
    if incident_fields is None:
        incident_fields = {}
    incidents_table = resource.Table(INCIDENTS_TABLE)
    incident = get_incident_by_id(incident_id)
    if incident:
        item = {**incident, **incident_fields, **{"updated": get_now()}}
    else:
        item = {
            **{"incidentId": incident_id, "created": get_now()},
            **incident_fields,
        }

    return incidents_table.put_item(Item=item)


def resolve_incident(incident_id):
    put_incident(incident_id, {RESOLVED_FIELD_NAME: get_now()})


def get_incident_by_id(incident_id, resolved=False):
    incidents = resource.Table(INCIDENTS_TABLE)
    response = incidents.query(
        KeyConditionExpression=Key("incidentId").eq(incident_id)
    )
    if response.get("Count", 0) > 0:
        incident = response.get("Items")[0]
        incident_resolved = incident.get(RESOLVED_FIELD_NAME, False)
        if not resolved or not incident_resolved:
            return incident


def get_issue_key_by_incident_id(incident_id):
    incident = get_incident_by_id(incident_id)
    if incident:
        return incident.get("issueKey")


def get_incident_id_by_issue_key(issue_key):
    incidents = resource.Table(INCIDENTS_TABLE)
    response = incidents.scan(FilterExpression=Attr("issueKey").eq(issue_key))
    if response.get("Count", 0) > 0:
        return response.get("Items")[0].get("incidentId")


def put_log_entry(log_entry_id):
    log_entries = resource.Table(LOG_ENTRIES_TABLE)
    return log_entries.put_item(Item={"logEntryId": log_entry_id})


def get_log_entry_by_id(log_entry_id):
    log_entries = resource.Table(LOG_ENTRIES_TABLE)
    response = log_entries.query(
        KeyConditionExpression=Key("logEntryId").eq(log_entry_id)
    )
    if response.get("Count", 0) > 0:
        return response.get("Items")[0].get("logEntryId")


def update_config_parameter(name, value):
    config_table = resource.Table(CONFIG_TABLE)

    return config_table.put_item(Item={
        "parameterName": name,
        "value": value
    })


def get_config_parameter(name):
    config_table = resource.Table(CONFIG_TABLE)

    response = config_table.query(
        KeyConditionExpression=Key(CONFIG_PARAMETER_FIELD_NAME).eq(name)
    )
    if response.get("Count", 0) > 0:
        return response.get("Items")[0].get(CONFIG_VALUE_FIELD_NAME)



def last_polling_timestamp():
    return get_config_parameter(LAST_POLLING_TIMESTAMP_PARAM)


def post_polling(timestamp = get_now(), result = None):
    return update_config_parameter(LAST_POLLING_TIMESTAMP_PARAM, get_now())


