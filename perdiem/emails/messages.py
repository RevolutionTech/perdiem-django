"""
:Created: 17 April 2016
:Author: Lucas Connors

"""

from django.conf import settings

from templated_email import send_templated_mail

from emails.exceptions import NoTemplateProvided
from emails.models import EmailSubscription
from emails.utils import create_unsubscribe_link


class BaseEmail(object):

    ignore_unsubscribed = False
    subscription_type = EmailSubscription.SUBSCRIPTION_ALL

    def unsubscribe_message(self, user):
        unsubscribe_url = create_unsubscribe_link(user, self.subscription_type)
        if self.subscription_type == EmailSubscription.SUBSCRIPTION_ALL:
            message = "To unsubscribe from all emails from PerDiem"
        else:
            message = "To unsubscribe from these types of emails from PerDiem"
        return {
            'plain': "{message}, go to: {url}.".format(message=message, url=unsubscribe_url),
            'html': "{message}, click <a href=\"{url}\">here</a>.".format(message=message, url=unsubscribe_url),
        }

    def get_template_name(self):
        if not hasattr(self, 'template_name'):
            raise NoTemplateProvided("No template was provided for the email message.")
        return self.template_name

    def get_context_data(self, user, **kwargs):
        context = {
            'user': user,
        }
        if not self.ignore_unsubscribed:
            context['unsubscribe_message'] = self.unsubscribe_message(user)
        return context

    def send_to_email(self, email, context={}):
        send_templated_mail(
            template_name=self.get_template_name(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            context=context
        )

    def send(self, user, context={}, **kwargs):
        context.update(self.get_context_data(user, **kwargs))
        if self.ignore_unsubscribed or EmailSubscription.objects.is_subscribed(user, subscription_type=self.subscription_type):
            self.send_to_email(user.email, context)


class WelcomeEmail(BaseEmail):

    template_name = 'welcome'


class ContactEmail(BaseEmail):

    template_name = 'contact'


class ArtistApplyEmail(BaseEmail):

    template_name = 'artist_apply'


class InvestSuccessEmail(BaseEmail):

    template_name = 'invest_success'

    def get_context_data(self, user, **kwargs):
        context = super(InvestSuccessEmail, self).get_context_data(user, **kwargs)

        investment = kwargs['investment']
        context.update({
            'artist': investment.campaign.artist,
            'campaign': investment.campaign,
            'num_shares': investment.num_shares,
        })

        return context
