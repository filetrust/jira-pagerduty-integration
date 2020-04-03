import datetime
import logging
import os

from jira.exceptions import JIRAError

import db
import utils


LOG_ENTRIES_ENDPOINT = '/log_entries'
logger = logging.getLogger(__name__)
TIMELINE_PROJECT_KEY = os.environ['TIMELINE_PROJECT_KEY']


def log_entries(event, context):
    pagerduty = utils.get_pagerduty()
    jira = utils.get_jira()
    params = {
        'since': datetime.datetime.now() - datetime.timedelta(hours=6)
    }
    log_entries = list(pagerduty.iter_all(LOG_ENTRIES_ENDPOINT, params=params))
    logger.debug('{} log entries found'.format(len(log_entries)))
    for log_entry in log_entries:
        if db.get_log_entry_by_id(log_entry['id']):
            msg = '[{}] Existing log entry found. Skipping...'
            msg = msg.format(log_entry['id'])
            logger.debug(msg)
            continue
        if log_entry['type'] == 'status_update_log_entry':
            logger.debug(
                '[{}] New status update found'.format(log_entry['id']))
            issue_key = db.get_issue_key_by_incident_id(
                log_entry['incident']['id'])
            if issue_key:
                logger.debug(
                    '[{}] Related issue found: {}'.format(
                        log_entry['id'], issue_key))
                try:
                    incident_issue = jira.issue(issue_key)
                except JIRAError as error:
                    logger.exception(
                        'Error occurred while retrieving Jira issue')
                else:
                    issue_dict = {
                        'project': {'key': os.environ['TIMELINE_PROJECT_KEY']},
                        'summary': log_entry['message'],
                        'issuetype': {'name': 'Bug'},
                    }
                    timeline_issue = jira.create_issue(fields=issue_dict)
                    utils.link_issue(
                        timeline_issue.key, issue_key, 'has timeline')
            else:
                logger.debug(
                    '[{}] Issue key not found'.format(log_entry['id']))
        db.put_log_entry(log_entry['id'])
    return {
        'ok': True,
    }
