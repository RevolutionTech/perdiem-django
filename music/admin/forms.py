"""
:Created: 9 October 2016
:Author: Lucas Connors

"""

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from pagedown.widgets import AdminPagedownWidget

from music.models import ActivityEstimate, AlbumBio, Track


class AlbumBioAdminForm(forms.ModelForm):

    bio = forms.CharField(
        help_text=AlbumBio._meta.get_field("bio").help_text, widget=AdminPagedownWidget
    )

    class Meta:
        model = AlbumBio
        fields = ("bio",)


class ActivityEstimateAdminForm(forms.ModelForm):
    class Meta:
        model = ActivityEstimate
        fields = ("date", "activity_type", "content_type", "object_id", "total")

    def clean(self):
        cleaned_data = super().clean()

        if not self.errors:
            # Get the object associated with this ActivityEstimate
            content_type = cleaned_data["content_type"]
            object_id = cleaned_data["object_id"]
            try:
                obj = content_type.get_object_for_this_type(id=object_id)
            except ObjectDoesNotExist:
                raise forms.ValidationError(
                    "The {object_name} with ID {invalid_id} does not exist.".format(
                        object_name=content_type.model, invalid_id=object_id
                    )
                )

            # Get the album associated with this ActivityEstimate
            if hasattr(obj, "album"):
                album = obj.album
            else:
                album = obj

            # Verify that the associated album has a campaign defined
            if not album.project.campaign_set.all().exists():
                raise forms.ValidationError(
                    "You cannot create activity estimates without defining the revenue percentages "
                    "issued to artists and fans. You must first create a campaign."
                )

        return cleaned_data


class DailyReportForm(forms.Form):

    track = forms.ModelChoiceField(
        queryset=Track.objects.all(), widget=forms.HiddenInput()
    )
    streams = forms.IntegerField(min_value=0)
    downloads = forms.IntegerField(min_value=0)
