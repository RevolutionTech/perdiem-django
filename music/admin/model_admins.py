"""
:Created: 9 October 2016
:Author: Lucas Connors

"""

from django.conf.urls import url
from django.contrib import admin

from music.admin.forms import ActivityEstimateAdminForm, AlbumBioAdminForm
from music.admin.views import DailyReportAdminView
from music.models import AlbumBio, Artwork, Audio, MarketplaceURL, Track


class TrackInline(admin.StackedInline):

    model = Track
    extra = 1


class ArtworkInline(admin.TabularInline):

    model = Artwork


class AlbumBioInline(admin.StackedInline):

    model = AlbumBio
    form = AlbumBioAdminForm


class MarketplaceURLInline(admin.TabularInline):

    model = MarketplaceURL


class AudioInline(admin.TabularInline):

    model = Audio


class AlbumAdmin(admin.ModelAdmin):

    raw_id_fields = ("project",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = (
        TrackInline,
        ArtworkInline,
        AlbumBioInline,
        MarketplaceURLInline,
        AudioInline,
    )


class ActivityEstimateAdmin(admin.ModelAdmin):

    list_display = ("content_object", "date", "activity_type")
    form = ActivityEstimateAdminForm

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r"^daily-report/?$",
                admin.site.admin_view(DailyReportAdminView.as_view()),
                name="daily_report",
            )
        ]
        return custom_urls + urls
