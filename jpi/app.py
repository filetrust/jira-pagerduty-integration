import logging

from flask import Flask, jsonify, request

from jpi import jirawebhook, webhooks, polling

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


try:
    # In some cases there is a need to use custom routes that are not
    # needed for the project but for development purposes only. If you
    # need them, please attach them to `dev_routes` blueprint that is
    # defined in the module `jpi.tools.dev_routes`.
    from jpi.tools.dev_routes import dev_routes
    app.register_blueprint(dev_routes)
except ImportError:
    pass
