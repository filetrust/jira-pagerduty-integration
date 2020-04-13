from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Attr, Key
import pytz

from jpi import settings


if settings.IS_OFFLINE:
    resource = boto3.resource(
        "dynamodb",
        region_name="localhost",
        endpoint_url=settings.DATABASE_ENDPOINT_URL,
    )
else:
    resource = boto3.resource("dynamodb")


def get_now():
    now = datetime.now(pytz.utc)
    return str(now)


def put_incident(incident_id, incident_fields=None):
    if incident_fields is None:
        incident_fields = {}
    incidents_table = resource.Table(settings.INCIDENTS_TABLE)
    incident = get_incident_by_id(incident_id)
    if incident:
        item = {**incident, **incident_fields, **{"updated": get_now()}}
    else:
        item = {
            **{"incidentId": incident_id, "created": get_now()},
            **incident_fields,
        }

    return incidents_table.put_item(Item=item)


def get_incident_by_id(incident_id, resolved=False):
    incidents = resource.Table(settings.INCIDENTS_TABLE)
    response = incidents.query(
        KeyConditionExpression=Key("incidentId").eq(incident_id)
    )
    if response.get("Count", 0) > 0:
        incident = response.get("Items")[0]
        incident_resolved = incident.get(settings.RESOLVED_FIELD_NAME, False)
        if not resolved or not incident_resolved:
            return incident


def get_issue_key_by_incident_id(incident_id):
    incident = get_incident_by_id(incident_id)
    if incident:
        return incident.get(settings.ISSUE_KEY_FIELD_NAME)


def get_incident_id_by_issue_key(issue_key):
    incidents = resource.Table(settings.INCIDENTS_TABLE)
    response = incidents.scan(
        FilterExpression=Attr(settings.ISSUE_KEY_FIELD_NAME).eq(issue_key)
    )
    if response.get("Count", 0) > 0:
        return response.get("Items")[0].get(settings.INCIDENT_ID_FIELD_NAME)


def put_log_entry(log_entry_id):
    log_entries = resource.Table(settings.LOG_ENTRIES_TABLE)
    return log_entries.put_item(
        Item={settings.LOG_ENTRY_ID_FIELD_NAME: log_entry_id}
    )


def get_log_entry_by_id(log_entry_id):
    log_entries = resource.Table(settings.LOG_ENTRIES_TABLE)
    response = log_entries.query(
        KeyConditionExpression=Key(settings.LOG_ENTRY_ID_FIELD_NAME).eq(
            log_entry_id
        )
    )
    if response.get("Count", 0) > 0:
        return response.get("Items")[0].get(settings.LOG_ENTRY_ID_FIELD_NAME)


def update_config_parameter(name, value):
    config_table = resource.Table(settings.CONFIG_TABLE)
    item = {
        settings.CONFIG_PARAMETER_FIELD_NAME: name,
        settings.CONFIG_VALUE_FIELD_NAME: value,
    }
    return config_table.put_item(Item=item)


def get_config_parameter(name):
    config_table = resource.Table(settings.CONFIG_TABLE)
    response = config_table.query(
        KeyConditionExpression=Key(settings.CONFIG_PARAMETER_FIELD_NAME).eq(
            name
        )
    )
    if response.get("Count", 0) > 0:
        return response.get("Items")[0].get(settings.CONFIG_VALUE_FIELD_NAME)

