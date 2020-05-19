"""
:Created: 17 April 2016
:Author: Lucas Connors

"""

from django.db import models
from django.dispatch import receiver
from pinax.stripe.models import Charge
from pinax.stripe.webhooks import registry

from emails.mailchimp import update_user_subscription
from emails.messages import InvestSuccessEmail
from emails.models import EmailSubscription


@receiver(
    models.signals.pre_save,
    sender=EmailSubscription,
    dispatch_uid="unsubscribe_from_all_handler",
)
def unsubscribe_from_all_handler(sender, instance, **kwargs):
    if (
        instance.subscription == EmailSubscription.SUBSCRIPTION_ALL
        and not instance.subscribed
    ):
        for email_subscription in EmailSubscription.objects.filter(
            user=instance.user
        ).exclude(id=instance.id):
            email_subscription.subscribed = False
            email_subscription.save()


@receiver(
    models.signals.pre_save,
    sender=EmailSubscription,
    dispatch_uid="sync_to_mailchimp_handler",
)
def sync_to_mailchimp_handler(sender, instance, **kwargs):
    user_is_subscribed_news = EmailSubscription.objects.is_subscribed(
        user=instance.user, subscription_type=EmailSubscription.SUBSCRIPTION_NEWS
    )
    if (
        instance.subscription == EmailSubscription.SUBSCRIPTION_NEWS
        and instance.subscribed != user_is_subscribed_news
    ):
        update_user_subscription(instance.user.email, instance.subscribed)


@receiver(registry.get_signal("charge.succeeded"))
def charge_succeeded_handler(sender, **kwargs):
    # Get investment this successful charge is related to
    charge_id = kwargs["event"].message["data"]["object"]["id"]
    charge = Charge.objects.get(stripe_id=charge_id)
    investment = charge.investment

    # Send out email for investing
    InvestSuccessEmail().send(user=investment.investor(), investment=investment)
