import factory
from django.apps import apps as django_apps

from accounts.factories import UserFactory
from artist.factories import artistfactory_factory


def projectfactory_factory(apps):
    class ProjectFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = apps.get_model("campaign", "Project")

        artist = factory.SubFactory(artistfactory_factory(apps=apps))

    return ProjectFactory


def campaignfactory_factory(apps, point_to_project=True):
    class CampaignFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = apps.get_model("campaign", "Campaign")

        amount = 10000
        fans_percentage = 20

        # Allow the CampaignFactory to point to the artist
        # for migration test cases before the Project model was created
        if point_to_project:
            project = factory.SubFactory(projectfactory_factory(apps=apps))
        else:
            artist = factory.SubFactory(artistfactory_factory(apps=apps))

    return CampaignFactory


def revenuereportfactory_factory(apps, point_to_project=True):
    class RevenueReportFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = apps.get_model("campaign", "RevenueReport")

        # Allow the RevenueReportFactory to point to a campaign directly
        # for migration test cases before the Project model was created
        if point_to_project:
            project = factory.SubFactory(projectfactory_factory(apps=apps))
        else:
            campaign = factory.SubFactory(campaignfactory_factory(apps=apps))

    return RevenueReportFactory


ProjectFactory = projectfactory_factory(apps=django_apps)
CampaignFactory = campaignfactory_factory(apps=django_apps)
RevenueReportFactory = revenuereportfactory_factory(apps=django_apps)


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django_apps.get_model("pinax_stripe", "Customer")

    user = factory.SubFactory(UserFactory)


class ChargeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django_apps.get_model("pinax_stripe", "Charge")

    customer = factory.SubFactory(CustomerFactory)
    paid = True
    refunded = False


class InvestmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django_apps.get_model("campaign", "Investment")

    charge = factory.SubFactory(ChargeFactory)
    campaign = factory.SubFactory(CampaignFactory)
