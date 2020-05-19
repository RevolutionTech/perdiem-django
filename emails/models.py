"""
:Created: 17 April 2016
:Author: Lucas Connors

"""

import uuid

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from emails.managers import EmailSubscriptionManager, VerifiedEmailManager


class VerifiedEmail(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    verified = models.BooleanField(default=False)
    code = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)

    objects = VerifiedEmailManager()

    def __str__(self):
        return self.email

    def url(self):
        return reverse(
            "verify_email", kwargs={"user_id": self.user.id, "code": self.code}
        )


class EmailSubscription(models.Model):

    SUBSCRIPTION_ALL = "ALL"
    SUBSCRIPTION_NEWS = "NEWS"
    SUBSCRIPTION_ARTUP = "ARTUP"
    SUBSCRIPTION_CHOICES = (
        (SUBSCRIPTION_ALL, "General"),
        (SUBSCRIPTION_NEWS, "Newsletter"),
        (SUBSCRIPTION_ARTUP, "Artist Updates"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.CharField(
        choices=SUBSCRIPTION_CHOICES, max_length=6, default=SUBSCRIPTION_ALL
    )
    subscribed = models.BooleanField(default=True)

    objects = EmailSubscriptionManager()

    class Meta:
        unique_together = (("user", "subscription"),)

    def __str__(self):
        return str(self.user)
