"""
:Created: 9 October 2016
:Author: Lucas Connors

"""

from django.contrib import messages
from django.urls import reverse

from music.admin.forms import DailyReportForm
from music.models import ActivityEstimate, Track
from perdiem.views import FormsetView


class DailyReportAdminView(FormsetView):

    template_name = "admin/music/activityestimate/daily-report.html"
    form_class = DailyReportForm

    def get_success_url(self):
        return reverse("admin:music_activityestimate_changelist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": "Enter Daily Report",
                "has_permission": self.request.user.is_superuser,
            }
        )
        return context

    def get_formset_factory_kwargs(self):
        num_tracks = Track.objects.all().count()
        return {
            "min_num": num_tracks,
            "max_num": num_tracks,
            "validate_min": True,
            "validate_max": True,
        }

    def get_initial(self):
        tracks = Track.objects.all().order_by("album__project__artist__name", "name")
        return [{"track": track} for track in tracks]

    def formset_valid(self, formset):
        for form in formset:
            d = form.cleaned_data
            track = d["track"]
            num_streams = d["streams"]
            num_downloads = d["downloads"]

            if num_streams:
                ActivityEstimate.objects.create(
                    activity_type=ActivityEstimate.ACTIVITY_STREAM,
                    content_object=track,
                    total=num_streams,
                )
            if num_downloads:
                ActivityEstimate.objects.create(
                    activity_type=ActivityEstimate.ACTIVITY_DOWNLOAD,
                    content_object=track,
                    total=num_downloads,
                )

        messages.success(self.request, "Daily Report was submitted successfully")
        return super().formset_valid(formset)
