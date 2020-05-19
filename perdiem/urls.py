"""
:Created: 26 July 2015
:Author: Lucas Connors

"""

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.views.static import serve

from accounts.views import (
    ContactFormView,
    ProfileView,
    PublicProfileView,
    VerifyEmailView,
    redirect_to_profile,
)
from artist.views import ArtistApplyFormView, ArtistDetailView, ArtistListView
from campaign.views import LeaderboardView
from emails.views import UnsubscribeView, unsubscribe_from_mailchimp
from music.views import AlbumDetailView, MusicListView

urlpatterns = [
    url(r"^health-check/?$", lambda r: HttpResponse(""), name="health_check"),
    url("", include(("social_django.urls", "social"))),
    url(r"^admin/", admin.site.urls),
    url(r"^api-auth/", include("rest_framework.urls")),
    url(r"^api/", include("api.urls")),
    url(r"^accounts/", include("accounts.urls")),
    url(
        r"^unsubscribe/from-mailchimp/$",
        unsubscribe_from_mailchimp,
        name="unsubscribe_from_mailchimp",
    ),
    url(
        r"^unsubscribe/(?P<user_id>\d+)/(?P<subscription_type>\w+)/(?P<token>[\w.:\-_=]+)/$",
        UnsubscribeView.as_view(),
        name="unsubscribe",
    ),
    url(
        r"^email/verify/(?P<user_id>\d+)/(?P<code>[\w-]+)/$",
        VerifyEmailView.as_view(),
        name="verify_email",
    ),
    url(r"^payments/", include("pinax.stripe.urls")),
    url(r"^artists/?$", ArtistListView.as_view(), name="artists"),
    url(r"^artist/apply/?$", ArtistApplyFormView.as_view(), name="artist_application"),
    url(
        r"^artist/apply/thanks/?$",
        TemplateView.as_view(template_name="artist/artist_application_thanks.html"),
        name="artist_application_thanks",
    ),
    url(r"^artist/(?P<slug>[\w_-]+)/?$", ArtistDetailView.as_view(), name="artist"),
    url(
        r"^artist/(?P<artist_slug>[\w_-]+)/(?P<album_slug>[\w_-]+)/?$",
        AlbumDetailView.as_view(),
        name="album",
    ),
    url(r"^music/?$", MusicListView.as_view(), name="music"),
    url(r"^profile/?$", ProfileView.as_view(), name="profile"),
    url(
        r"^profile/(?P<username>[\w.@+-]+)/?$",
        PublicProfileView.as_view(),
        name="public_profile",
    ),
    url(r"^stats/?$", LeaderboardView.as_view(), name="leaderboard"),
    url(
        r"^artist-resources/?$",
        TemplateView.as_view(template_name="extra/artist-resources.html"),
        name="artist-resources",
    ),
    url(
        r"^terms/?$",
        TemplateView.as_view(template_name="extra/terms.html"),
        name="terms",
    ),
    url(
        r"^trust/?$",
        TemplateView.as_view(template_name="extra/trust.html"),
        name="trust",
    ),
    url(
        r"^privacy/?$",
        TemplateView.as_view(template_name="extra/privacy.html"),
        name="privacy",
    ),
    url(
        r"^investor-resources/?$",
        TemplateView.as_view(template_name="extra/investor-resources.html"),
        name="investor-resources",
    ),
    url(
        r"^funding/?$",
        TemplateView.as_view(template_name="extra/funding.html"),
        name="funding",
    ),
    url(r"^faq/?$", TemplateView.as_view(template_name="extra/faq.html"), name="faq"),
    url(
        r"^contact/thanks/?$",
        TemplateView.as_view(template_name="registration/contact_thanks.html"),
        name="contact_thanks",
    ),
    url(r"^contact/?$", ContactFormView.as_view(), name="contact"),
    url(r"^$", TemplateView.as_view(template_name="home.html"), name="home"),
    url(r"^(?P<slug>[\w.@+_-]+)/?$", redirect_to_profile),
]

# Add media folder to urls when DEBUG = True
if settings.DEBUG:
    urlpatterns.append(
        url(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})
    )
