# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-18 23:52
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0007_auto_20160618_2352'),
    ]

    def point_artistpercentagebreakdown_to_project(apps, schema_editor):
        ArtistPercentageBreakdown = apps.get_model("campaign", "ArtistPercentageBreakdown")
        for artistpercentagebreakdown in ArtistPercentageBreakdown.objects.all():
            artistpercentagebreakdown.project = artistpercentagebreakdown.campaign.project
            artistpercentagebreakdown.save()

    def point_artistpercentagebreakdown_to_campaign(apps, schema_editor):
        ArtistPercentageBreakdown = apps.get_model("campaign", "ArtistPercentageBreakdown")
        for artistpercentagebreakdown in ArtistPercentageBreakdown.objects.all():
            artistpercentagebreakdown.campaign = artistpercentagebreakdown.project.campaign_set.first()
            artistpercentagebreakdown.save()

    def point_revenuereport_to_project(apps, schema_editor):
        RevenueReport = apps.get_model("campaign", "RevenueReport")
        for revenuereport in RevenueReport.objects.all():
            revenuereport.project = revenuereport.campaign.project
            revenuereport.save()

    def point_revenuereport_to_campaign(apps, schema_editor):
        RevenueReport = apps.get_model("campaign", "RevenueReport")
        for revenuereport in RevenueReport.objects.all():
            revenuereport.campaign = revenuereport.project.campaign_set.first()
            revenuereport.save()

    operations = [
        migrations.RunPython(point_artistpercentagebreakdown_to_project, point_artistpercentagebreakdown_to_campaign),
        migrations.RunPython(point_revenuereport_to_project, point_revenuereport_to_campaign),
    ]
