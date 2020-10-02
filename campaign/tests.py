"""
:Created: 12 March 2016
:Author: Lucas Connors

"""

import datetime

import factory
from django.test import TestCase
from pigeon.test import RenderTestCase

from artist.factories import ArtistFactory
from campaign.factories import (
    CampaignFactory,
    ProjectFactory,
    RevenueReportFactory,
    campaignfactory_factory,
    revenuereportfactory_factory,
)
from perdiem.tests import MigrationTestCase, PerDiemTestCase


class CreateInitialProjectsMigrationTestCase(MigrationTestCase):

    migrate_from = "0005_auto_20160618_2310"
    migrate_to = "0006_auto_20160618_2351"

    def setUpBeforeMigration(self, apps):
        # Create a campaign
        CampaignFactoryForMigrationTestCase = campaignfactory_factory(
            apps=apps, point_to_project=False
        )
        self.campaign = CampaignFactoryForMigrationTestCase()

    def testProjectsCreatedFromCampaigns(self):
        Project = self.apps.get_model("campaign", "Project")

        # Verify that a project was created from the campaign
        self.assertEqual(Project.objects.count(), 1)

        # Verify that the project reason comes from the campaign reason
        project = Project.objects.get()
        self.assertEqual(project.reason, self.campaign.reason)


class PointArtistPercentageBreakdownsAndRevenueReportsToProjectsMigrationTestCase(
    MigrationTestCase
):

    migrate_from = "0007_auto_20160618_2352"
    migrate_to = "0008_auto_20160618_2352"

    def setUpBeforeMigration(self, apps):
        CampaignFactoryForMigrationTestCase = campaignfactory_factory(apps=apps)
        RevenueReportFactoryForMigrationTestCase = revenuereportfactory_factory(
            apps=apps, point_to_project=False
        )

        class ArtistPercentageBreakdownFactoryForMigrationTestCase(
            factory.django.DjangoModelFactory
        ):
            class Meta:
                model = apps.get_model("campaign", "ArtistPercentageBreakdown")

            campaign = factory.SubFactory(CampaignFactoryForMigrationTestCase)

        # Create a RevenueReport and ArtistPercentageBreakdown
        self.revenue_report = RevenueReportFactoryForMigrationTestCase(amount=1000)
        campaign = self.revenue_report.campaign
        self.artistpercentagebreakdown = (
            ArtistPercentageBreakdownFactoryForMigrationTestCase(
                campaign=campaign, percentage=50
            )
        )

    def testArtistPercentageBreakdownAndRevenueReportPointsToProject(self):
        Campaign = self.apps.get_model("campaign", "Campaign")
        campaign = Campaign.objects.get()
        self.artistpercentagebreakdown.refresh_from_db()
        self.assertEqual(self.artistpercentagebreakdown.project.id, campaign.project.id)
        self.revenue_report.refresh_from_db()
        self.assertEqual(self.revenue_report.project.id, campaign.project.id)


class CampaignModelTestCase(TestCase):
    def testProjectGeneratedRevenue(self):
        # Generate campaign and revenue report
        campaign = CampaignFactory()
        revenue_report = RevenueReportFactory(project=campaign.project, amount=100)

        # Verify that the amount generated is considered revenue for the project
        self.assertEqual(revenue_report.project.generated_revenue(), 100)
        self.assertEqual(revenue_report.project.generated_revenue_fans(), 20)

    def testCampaignRaisingZeroIsAlreadyFunded(self):
        campaign = CampaignFactory(amount=0)
        self.assertEqual(campaign.percentage_funded(), 100)


class CampaignAdminWebTestCase(PerDiemTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.project = ProjectFactory()
        start_datetime = datetime.datetime(year=2017, month=2, day=1)
        end_datetime = datetime.datetime(year=2017, month=3, day=1)
        cls.campaign_add_data = {
            "project": cls.project.id,
            "amount": 10000,
            "value_per_share": 1,
            "start_datetime_0": start_datetime.strftime("%Y-%m-%d"),
            "start_datetime_1": start_datetime.strftime("%H:%M:%S"),
            "end_datetime_0": end_datetime.strftime("%Y-%m-%d"),
            "end_datetime_1": end_datetime.strftime("%H:%M:%S"),
            "use_of_funds": "",
            "fans_percentage": 50,
            "expense_set-TOTAL_FORMS": 0,
            "expense_set-INITIAL_FORMS": 0,
        }

    def testProjectAdminRenders(self):
        # Create a campaign for the project
        CampaignFactory(project=self.project)

        # Verify that the change project page on admin renders
        self.assertResponseRenders(
            "/admin/campaign/project/{project_id}/change/".format(
                project_id=self.project.id
            )
        )

    def testAddCampaign(self):
        self.assertResponseRedirects(
            "/admin/campaign/campaign/add/",
            "/admin/campaign/campaign/",
            method="POST",
            data=self.campaign_add_data,
        )

    def testCampaignEndCannotComeBeforeStart(self):
        # Set the end datetime to a value from the past
        data = self.campaign_add_data.copy()
        end_datetime = datetime.datetime(year=2017, month=1, day=1)
        data.update(
            {
                "end_datetime_0": end_datetime.strftime("%Y-%m-%d"),
                "end_datetime_1": end_datetime.strftime("%H:%M:%S"),
            }
        )

        # Campaigns cannot be added that have an end datetime before the start
        response = self.assertResponseRenders(
            "/admin/campaign/campaign/add/",
            method="POST",
            data=data,
            has_form_error=True,
        )
        self.assertIn(b"Campaign cannot end before it begins.", response.content)

    def testCannotAddCampaignWithoutTime(self):
        for dt in ["start", "end"]:
            # Erase the time from campaign add POST data
            data = self.campaign_add_data.copy()
            del data[f"{dt}_datetime_1"]

            # Fail to create a campaign without the time component
            self.assertResponseRenders(
                "/admin/campaign/campaign/add/",
                method="POST",
                data=data,
                has_form_error=True,
            )


class CampaignWebTestCase(PerDiemTestCase):
    def get200s(self):
        return ["/stats/"]
