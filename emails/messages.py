"""
:Created: 17 April 2016
:Author: Lucas Connors

"""

from django.conf import settings
from django.contrib.sites.models import Site
from templated_email import send_templated_mail

from emails.exceptions import NoTemplateProvided
from emails.models import EmailSubscription, VerifiedEmail
from emails.utils import create_unsubscribe_link


class BaseEmail:

    from_email = settings.DEFAULT_FROM_EMAIL
    ignore_unsubscribed = False
    send_to_unverified_emails = False
    subscription_type = EmailSubscription.SUBSCRIPTION_ALL

    @staticmethod
    def get_host():
        return "{proto}://{domain}".format(
            proto="http" if settings.DEBUG else "https",
            domain=Site.objects.get_current().domain,
        )

    def unsubscribe_message(self, user):
        host = self.get_host()
        unsubscribe_url = create_unsubscribe_link(user, self.subscription_type)
        if self.subscription_type == EmailSubscription.SUBSCRIPTION_ALL:
            message = "To unsubscribe from all emails from PerDiem"
        else:
            message = "To unsubscribe from these emails"
        return {
            "plain": "{message}, go to: {host}{url}.".format(
                message=message, host=host, url=unsubscribe_url
            ),
            "html": '{message}, click <a href="{host}{url}">here</a>.'.format(
                message=message, host=host, url=unsubscribe_url
            ),
        }

    def get_template_name(self):
        if not hasattr(self, "template_name"):
            raise NoTemplateProvided("No template was provided for the email message.")
        return self.template_name

    def get_from_email_address(self, **kwargs):
        return self.from_email

    def get_context_data(self, user, **kwargs):
        context = {"host": self.get_host(), "user": user}
        if not self.ignore_unsubscribed:
            context["unsubscribe_message"] = self.unsubscribe_message(user)
        return context

    def send_to_email(self, email, context=None, **kwargs):
        """
        This method is not meant to be called directly, except for
        sending emails to email addresses that do not belong to a user.
        Generally, this method should be called from the send() method.
        """
        context = context or {}
        send_templated_mail(
            template_name=self.get_template_name(),
            from_email=self.get_from_email_address(**kwargs),
            recipient_list=[email],
            context=context,
        )

    def send(self, user, context=None, **kwargs):
        context = context or {}
        context.update(self.get_context_data(user, **kwargs))
        user_is_subscribed = EmailSubscription.objects.is_subscribed(
            user, subscription_type=self.subscription_type
        )
        user_subscription_okay = self.ignore_unsubscribed or user_is_subscribed
        email_is_verified = (
            self.send_to_unverified_emails
            or VerifiedEmail.objects.is_current_email_verified(user)
        )
        if user_subscription_okay and email_is_verified:
            self.send_to_email(user.email, context, **kwargs)


class EmailVerificationEmail(BaseEmail):

    template_name = "email_verification"
    send_to_unverified_emails = True

    def get_context_data(self, user, **kwargs):
        context = super().get_context_data(user, **kwargs)
        context["verify_email_url"] = VerifiedEmail.objects.get_current_email(
            user
        ).url()
        return context


class WelcomeEmail(EmailVerificationEmail):

    template_name = "welcome"

    def get_context_data(self, user, **kwargs):
        context = super().get_context_data(user, **kwargs)
        verified_email = VerifiedEmail.objects.get_current_email(user)
        if verified_email.verified:
            del context["verify_email_url"]
        return context


class ContactEmail(BaseEmail):

    template_name = "contact"


class ArtistApplyEmail(BaseEmail):

    template_name = "artist_apply"


class ArtistUpdateEmail(BaseEmail):

    template_name = "artist_update"
    subscription_type = EmailSubscription.SUBSCRIPTION_ARTUP

    def get_from_email_address(self, **kwargs):
        update = kwargs["update"]
        return "{artist_name} <noreply@investperdiem.com>".format(
            artist_name=update.artist.name
        )

    def get_context_data(self, user, **kwargs):
        context = super().get_context_data(user, **kwargs)

        update = kwargs["update"]
        context.update({"artist": update.artist, "update": update})

        return context


class InvestSuccessEmail(BaseEmail):

    template_name = "invest_success"

    def get_context_data(self, user, **kwargs):
        context = super().get_context_data(user, **kwargs)

        investment = kwargs["investment"]
        context.update(
            {
                "artist": investment.campaign.project.artist,
                "campaign": investment.campaign,
                "num_shares": investment.num_shares,
            }
        )

        return context
