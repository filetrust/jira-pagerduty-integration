import logging

from flask import Flask, jsonify, request

from jpi import jirawebhook, pd_cron, webhooks, polling

app = Flask(__name__)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@app.route("/pagerduty-webhook", methods=["POST"])
def pagerduty_webhook():
    response = {"ok": True}
    try:
        webhooks.pagerduty(request.json)
    except Exception as e:
        logger.exception(
            "Error occurred during processing of a PagerDuty webhook"
        )
        response = {"ok": False, "error": repr(e)}
    return jsonify(response)


@app.route("/jira-webhook", methods=["POST"])
def jira_webhook():
    response = {"ok": True}
    try:
        jirawebhook.jira(request.json)
    except Exception as e:
        logger.exception("Error occurred during processing of a Jira webhook")
        response = {"ok": False, "error": repr(e)}
    return jsonify(response)


# The handler serves to 'manually' run of the cron function. It's useful for
# development and/or support
@app.route("/pagerduty-sync", methods=["POST"])
def cron():
    try:
        response = pd_cron.handler(None, None)
        response["ok"] = True
    except Exception as e:
        logger.exception(
            "Error occurred during processing of a PagerDuty sync"
        )
        response = {"ok": False, "error": repr(e)}
    return jsonify(response)


# The handler serves to 'manually' run of the polling function. It's useful for
# development and/or support
@app.route("/pagerduty-poll", methods=["POST"])
def polling_handler():
    try:
        response = polling.handler(None, None)
        response["ok"] = True
    except Exception as e:
        logger.exception(
            "Error occurred during processing of a PagerDuty poll"
        )
        response = {"ok": False, "error": repr(e)}
    return jsonify(response)
