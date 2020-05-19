"""
:Created: 14 May 2016
:Author: Lucas Connors

"""

import hashlib

import requests
from django.conf import settings


class MailChimpException(Exception):
    def __init__(self, status_code, title, detail, type):
        message = "{status_code} {title}: {detail}\nMore information: {type}".format(
            status_code=status_code, title=title, detail=detail, type=type
        )
        super().__init__(message)


def update_user_subscription(email, subscribed):
    mailchimp_api_key = settings.MAILCHIMP_API_KEY
    mailchimp_data_center = mailchimp_api_key.split("-")[-1]
    url = "https://{dc}.api.mailchimp.com/3.0/lists/{list_id}/members/{subscriber_hash}".format(
        dc=mailchimp_data_center,
        list_id=settings.MAILCHIMP_LIST_ID,
        subscriber_hash=hashlib.md5(email.lower().encode("utf-8")).hexdigest(),
    )
    status = "subscribed" if subscribed else "unsubscribed"
    data = {"email_address": email, "status": status}
    response = requests.put(url, json=data, auth=("", mailchimp_api_key))
    if response.status_code >= 400:
        response_json = response.json()
        raise MailChimpException(
            status_code=response.status_code,
            title=response_json["title"],
            detail=response_json["detail"],
            type=response_json["type"],
        )
