import factory
from django.apps import apps

from accounts.factories import UserFactory


class EmailSubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = apps.get_model("emails", "EmailSubscription")

    user = factory.SubFactory(UserFactory)
