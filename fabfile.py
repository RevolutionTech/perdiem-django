"""
:Created: 31 May 2016
:Author: Lucas Connors

"""

import os

import requests
from fabric import task

PROJECT_DIR = "~/perdiem-django"
REMOTE_HOSTS = os.environ.get("PERDIEM_REMOTE_HOSTS", "").split(",")

remote_task = task(hosts=REMOTE_HOSTS)


def _pull_latest_changes(cxn):
    """
    Pull latest code from origin
    :return: Description of the changes since the last deploy
    """
    with cxn.cd(PROJECT_DIR):
        previous_commit_hash = cxn.run(
            "git rev-parse HEAD", hide="stdout"
        ).stdout.strip()
        cxn.run("git pull", echo=True)
        cmd_changes_pulled = (
            f"git log {previous_commit_hash}.. "
            f'--reverse --first-parent --format="%h : %an : %s" --no-color'
        )
        changes_pulled = cxn.run(cmd_changes_pulled, hide="stdout").stdout.strip()
    return changes_pulled


def _perform_update(cxn):
    """
    Update dependencies, run migrations, etc.
    """
    with cxn.prefix("export PATH=$HOME/.pyenv/bin:$HOME/.poetry/bin:$PATH"), cxn.cd(
        PROJECT_DIR
    ), cxn.prefix('eval "$(pyenv init -)"'):
        cxn.run("poetry install --no-dev", echo=True)
        cxn.run("poetry run python manage.py migrate", echo=True)
        cxn.run("poetry run python manage.py collectstatic --no-input", echo=True)


def _send_notification(commits, deploy_successful):
    """
    Post update to Slack
    """
    bot_token = os.environ.get("PERDIEM_DEPLOYBOT_TOKEN")
    if not bot_token:
        return

    if commits:
        if deploy_successful:
            deploy_status = "completed successfully"
        else:
            deploy_status = "started, but was not completed successfully"
        text = f"Deploy {deploy_status}. Changelog:\n```\n{commits}\n```"
    elif deploy_successful:
        text = "Services were restarted successfully."
    else:
        text = "Attempted to restart services, but a failure occurred."

    data = {"token": bot_token, "channel": "#general", "text": text, "as_user": True}
    requests.post("https://slack.com/api/chat.postMessage", data=data)


@remote_task
def restart(cxn):
    """
    Restart services
    """
    cxn.sudo("sv restart perdiem", echo=True)
    cxn.sudo("service nginx restart", echo=True)


@remote_task
def deploy(cxn):
    """
    Perform update, restart services, and send notification to Slack
    """
    changes_pulled = _pull_latest_changes(cxn)

    deploy_successful = False
    try:
        _perform_update(cxn)
        restart(cxn)
        deploy_successful = True
    finally:
        _send_notification(changes_pulled, deploy_successful)
