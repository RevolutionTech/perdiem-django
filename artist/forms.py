"""
:Created: 19 March 2016
:Author: Lucas Connors

"""

from django import forms
from pagedown.widgets import PagedownWidget


class ArtistApplyForm(forms.Form):

    artist_name = forms.CharField(label="Artist / Band Name")
    photo_link = forms.URLField(
        label="Artist Profile Photo (Download URL)",
        widget=forms.TextInput(attrs={"placeholder": "http://"}),
    )
    genre = forms.CharField()
    location = forms.CharField()
    email = forms.EmailField()
    phone_number = forms.CharField()
    bio = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "We started playing music because..."}
        )
    )
    project = forms.CharField(
        label="Project Name",
        widget=forms.TextInput(attrs={"placeholder": "Single/Album Name"}),
    )
    campaign_reason = forms.CharField(
        label="What are you raising money for?",
        widget=forms.Textarea(
            attrs={"placeholder": "We are raising money to promote our album..."}
        ),
    )
    amount_raising = forms.CharField(
        label="Amount Raising", widget=forms.TextInput(attrs={"placeholder": "$1,000"})
    )
    giving_back = forms.CharField(
        label="% Back To Investors",
        widget=forms.TextInput(attrs={"placeholder": "50%"}),
    )
    campaign_start = forms.DateField(
        label="Campaign Start Date",
        widget=forms.TextInput(attrs={"placeholder": "MM/DD/YYYY"}),
    )
    campaign_end = forms.DateField(
        label="Campaign End Date",
        widget=forms.TextInput(attrs={"placeholder": "MM/DD/YYYY"}),
    )
    payback_period = forms.CharField(
        label="How long you want to pay back investors",
        widget=forms.TextInput(attrs={"placeholder": "5 years, 10 years, 20 years..."}),
    )
    soundcloud = forms.URLField(
        label="SoundCloud", widget=forms.TextInput(attrs={"placeholder": "http://"})
    )
    spotify = forms.URLField(
        required=False,
        label="Spotify",
        widget=forms.TextInput(attrs={"placeholder": "http://"}),
    )
    facebook = forms.URLField(
        required=False, widget=forms.TextInput(attrs={"placeholder": "http://"})
    )
    twitter = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"placeholder": "@"})
    )
    instagram = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"placeholder": "@"})
    )
    terms = forms.BooleanField(
        label="Terms & Conditions",
        help_text="I have read and agree to the Terms & Conditions",
    )


class ArtistUpdateForm(forms.Form):

    title = forms.CharField(max_length=75)
    text = forms.CharField(widget=PagedownWidget())
    image = forms.ImageField(required=False)
    youtube_url = forms.URLField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data["image"]
        youtube_url = cleaned_data["youtube_url"]
        provided = list(filter(lambda x: x, [image, youtube_url]))
        if len(provided) > 1:
            raise forms.ValidationError("Please only provide one image or video.")
        return cleaned_data
