"""
:Created: 19 March 2016
:Author: Lucas Connors

"""

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from geopy.exc import GeocoderTimedOut

from artist.forms import ArtistApplyForm, ArtistUpdateForm
from artist.geolocator import geolocator
from artist.models import Artist, Genre, Update, UpdateImage, UpdateMediaURL
from emails.messages import ArtistApplyEmail, ArtistUpdateEmail


class ArtistListView(ListView):

    template_name = "artist/artist_list.html"
    context_object_name = "artists"

    ORDER_BY_NAME = {
        "recent": "Recently Added",
        "funded": "% Funded",
        "time-remaining": "Time to Go",
        "investors": "# Investors",
        "raised": "Amount Raised",
        "valuation": "Valuation",
    }
    ORDER_BY_METHOD = {
        "funded": "order_by_percentage_funded",
        "time-remaining": "order_by_time_remaining",
        "investors": "order_by_num_investors",
        "raised": "order_by_amount_raised",
        "valuation": "order_by_valuation",
    }

    def dispatch(self, request, *args, **kwargs):
        # Filtering
        self.active_genre = request.GET.get("genre", "All Genres")
        self.distance = request.GET.get("distance")
        self.location = request.GET.get("location")
        self.lat = request.GET.get("lat")
        self.lon = request.GET.get("lon")

        # Sorting
        order_by_slug = request.GET.get("sort")
        if order_by_slug not in self.ORDER_BY_NAME:
            order_by_slug = "recent"
        self.order_by = {
            "slug": order_by_slug,
            "name": self.ORDER_BY_NAME[order_by_slug],
        }

        # Geolocate if location
        self.location_coordinates = None
        self.geocoder_failed = False
        if self.location:
            try:
                self.location_coordinates = geolocator.geocode(self.location)
            except GeocoderTimedOut:
                self.geocoder_failed = True

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort_options = [{"slug": s, "name": n} for s, n in self.ORDER_BY_NAME.items()]
        context.update(
            {
                "genres": Genre.objects.all()
                .order_by("name")
                .values_list("name", flat=True),
                "active_genre": self.active_genre,
                "distance": self.distance
                if (self.lat and self.lon) or self.location
                else None,
                "location": self.location,
                "lat": self.lat,
                "lon": self.lon,
                "geocoder_failed": self.geocoder_failed,
                "sort_options": sorted(sort_options, key=lambda o: o["name"]),
                "order_by": self.order_by,
            }
        )
        return context

    def filter_by_location(self, artists):
        if self.distance and (
            (self.lat and self.lon) or (self.location and self.location_coordinates)
        ):
            if self.lat and self.lon:
                lat, lon = self.lat, self.lon
            elif self.location and self.location_coordinates:
                lat, lon = (
                    self.location_coordinates.latitude,
                    self.location_coordinates.longitude,
                )
            artists = artists.filter_by_location(
                distance=int(self.distance), lat=lat, lon=lon
            )
        return artists

    def sort_artists(self, artists):
        order_by_name = self.order_by["slug"]
        if order_by_name in self.ORDER_BY_METHOD:
            return getattr(artists, self.ORDER_BY_METHOD[order_by_name])
        return artists.order_by("-id")

    def get_queryset(self):
        artists = Artist.objects.all()
        artists = artists.filter_by_genre(self.active_genre)
        artists = self.filter_by_location(artists)
        artists = artists.exclude_failed_artists()
        artists = self.sort_artists(artists)
        return artists


class ArtistDetailView(FormView):

    template_name = "artist/artist_detail.html"
    form_class = ArtistUpdateForm

    def get_success_url(self):
        return reverse("artist", kwargs={"slug": self.slug})

    def dispatch(self, request, *args, **kwargs):
        self.slug = kwargs["slug"]
        self.artist = get_object_or_404(Artist, slug=self.slug)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        user_has_permission_to_submit_update = (
            self.artist.has_permission_to_submit_update(self.request.user)
        )
        context.update(
            {
                "PINAX_STRIPE_PUBLIC_KEY": settings.PINAX_STRIPE_PUBLIC_KEY,
                "PERDIEM_PERCENTAGE": settings.PERDIEM_PERCENTAGE,
                "STRIPE_PERCENTAGE": settings.STRIPE_PERCENTAGE,
                "STRIPE_FLAT_FEE": settings.STRIPE_FLAT_FEE,
                "DEFAULT_MIN_PURCHASE": settings.DEFAULT_MIN_PURCHASE,
                "has_permission_to_submit_update": user_has_permission_to_submit_update,
            }
        )

        context["artist"] = self.artist
        investors = self.artist.investors()
        context["investors"] = sorted(
            investors.values(),
            key=lambda investor: investor["total_investment"],
            reverse=True,
        )

        campaign = self.artist.active_campaign()
        if campaign:
            context["campaign"] = campaign
            context["fans_percentage"] = context[
                "fans_percentage_display"
            ] = campaign.project.total_fans_percentage()

            if self.request.user.is_authenticated:
                user_investor = investors.get(self.request.user.id)
                if user_investor:
                    user_investor["percentage_display"] = max(
                        0.5, user_investor.get("percentage", 0)
                    )
                    context["fans_percentage"] -= user_investor["percentage"]
                    context["fans_percentage_display"] -= user_investor[
                        "percentage_display"
                    ]
                    context["user_investor"] = user_investor

        user_is_investor = (
            self.request.user.is_authenticated
            and self.artist.is_investor(self.request.user)
        )
        if user_has_permission_to_submit_update or user_is_investor:
            context["updates"] = self.artist.update_set.all().order_by(
                "-created_datetime"
            )
        context["latest_campaign"] = self.artist.latest_campaign()

        return context

    def form_valid(self, form):
        d = form.cleaned_data

        # Verify that the user has permission
        if not self.artist.has_permission_to_submit_update(self.request.user):
            return HttpResponseForbidden()

        # Create the base update
        update = Update.objects.create(
            artist=self.artist, title=d["title"], text=d["text"]
        )

        # Attach images/videos to the update
        image = d["image"]
        if image:
            UpdateImage.objects.create(update=update, img=image)
        youtube_url = d["youtube_url"]
        if youtube_url:
            UpdateMediaURL.objects.create(
                update=update, media_type=UpdateMediaURL.MEDIA_YOUTUBE, url=youtube_url
            )

        # Send email to users following the artist's updates
        investors = User.objects.filter(
            customer__charges__paid=True,
            customer__charges__refunded=False,
            customer__charges__investment__campaign__project__artist=self.artist,
        ).distinct()
        for investor in investors:
            ArtistUpdateEmail().send(user=investor, update=update)

        return super().form_valid(form)


class ArtistApplyFormView(FormView):

    template_name = "artist/artist_application.html"
    form_class = ArtistApplyForm

    def get_success_url(self):
        return reverse("artist_application_thanks")

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        if user.is_authenticated:
            initial["email"] = user.email
        return initial

    def form_valid(self, form):
        # Add user_id to context, if available
        context = form.cleaned_data
        user = self.request.user
        if user.is_authenticated:
            context["user_id"] = user.id

        # Send artist application email
        ArtistApplyEmail().send_to_email(
            email="info@investperdiem.com", context=context
        )

        return super().form_valid(form)
