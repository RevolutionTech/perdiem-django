"""
:Created: 12 March 2016
:Author: Lucas Connors

"""

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextInputWidget
from django.template.loader import render_to_string
from pagedown.widgets import AdminPagedownWidget

from artist.models import Artist, ArtistAdmin, Bio, Genre, Photo, Playlist, Social


class LocationWidget(AdminTextInputWidget):

    # TODO: Use template_name and refactor widget to use Django 1.11's new get_context() method
    # https://docs.djangoproject.com/en/1.11/ref/forms/widgets/#django.forms.Widget.get_context
    template_name_dj110_to_dj111_compat = "widgets/coordinates.html"

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs=attrs, renderer=renderer)
        return html + render_to_string(self.template_name_dj110_to_dj111_compat)


class ArtistAdminForm(forms.ModelForm):

    location = forms.CharField(
        help_text=Artist._meta.get_field("location").help_text, widget=LocationWidget
    )

    class Meta:
        model = Artist
        fields = ("name", "genres", "slug", "location", "lat", "lon")


class ArtistAdministratorInline(admin.StackedInline):

    model = ArtistAdmin
    raw_id_fields = ("user",)
    extra = 2


class BioAdminForm(forms.ModelForm):

    bio = forms.CharField(
        help_text=Bio._meta.get_field("bio").help_text, widget=AdminPagedownWidget
    )

    class Meta:
        model = Bio
        fields = ("bio",)


class BioInline(admin.StackedInline):

    model = Bio
    form = BioAdminForm


class PhotoInline(admin.TabularInline):

    model = Photo


class PlaylistInline(admin.TabularInline):

    model = Playlist
    extra = 1


class SocialInline(admin.TabularInline):

    model = Social


class ArtistAdmin(admin.ModelAdmin):

    form = ArtistAdminForm
    prepopulated_fields = {"slug": ("name",)}
    inlines = (
        ArtistAdministratorInline,
        BioInline,
        PhotoInline,
        PlaylistInline,
        SocialInline,
    )


admin.site.register(Genre)
admin.site.register(Artist, ArtistAdmin)
