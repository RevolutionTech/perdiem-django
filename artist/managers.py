"""
:Created: 1 May 2016
:Author: Lucas Connors

"""

import geopy
from django.db import models
from django.utils import timezone
from geopy.distance import distance as calc_distance


class ArtistQuerySet(models.QuerySet):
    @staticmethod
    def bounding_coordinates(distance, lat, lon):
        origin = geopy.Point((lat, lon))
        geopy_distance = calc_distance(miles=distance)
        min_lat = geopy_distance.destination(origin, 180).latitude
        max_lat = geopy_distance.destination(origin, 0).latitude
        min_lon = geopy_distance.destination(origin, 270).longitude
        max_lon = geopy_distance.destination(origin, 90).longitude
        return min_lat, max_lat, min_lon, max_lon

    @staticmethod
    def percentage_funded(artist):
        campaign = artist.latest_campaign()
        if campaign:
            funded = campaign.percentage_funded()
            artist.funded = funded
            return funded

    @staticmethod
    def valuation(artist):
        campaign = artist.latest_campaign()
        if campaign:
            valuation = campaign.valuation()
            artist.valuation = valuation
            return valuation

    def filter_by_genre(self, genre):
        if genre != "All Genres":
            return self.filter(genres__name=genre)
        return self.all()

    # TODO(lucas): Use annotations as much as possible to improve performance
    def filter_by_funded(self):
        funded_artist_ids = []
        for artist in self:
            campaign = artist.latest_campaign()
            if campaign and campaign.percentage_funded() == 100:
                funded_artist_ids.append(artist.id)

        return self.filter(id__in=funded_artist_ids)

    def filter_by_location(self, distance, lat, lon):
        min_lat, max_lat, min_lon, max_lon = self.bounding_coordinates(
            distance, lat, lon
        )
        artists_within_bounds = self.filter(
            lat__gte=min_lat, lat__lte=max_lat, lon__gte=min_lon, lon__lte=max_lon
        )

        nearby_artist_ids = []
        for artist in artists_within_bounds:
            if calc_distance((lat, lon), (artist.lat, artist.lon)).miles <= distance:
                nearby_artist_ids.append(artist.id)
        return self.filter(id__in=nearby_artist_ids)

    # TODO(lucas): Use annotations as much as possible to improve performance
    def exclude_failed_artists(self):
        excluded_artist_ids = []
        for artist in self:
            if artist.all_campaigns_failed():
                excluded_artist_ids.append(artist.id)

        return self.exclude(id__in=excluded_artist_ids)

    # TODO(lucas): Use annotations as much as possible to improve performance
    def order_by_percentage_funded(self):
        return sorted(
            self, key=lambda artist: self.percentage_funded(artist) or 0, reverse=True
        )

    def order_by_time_remaining(self):
        artists = self.annotate(
            campaign_end_datetime=models.Max("project__campaign__end_datetime")
        )
        artists_current_campaign = artists.filter(
            campaign_end_datetime__gte=timezone.now()
        ).order_by("campaign_end_datetime")
        artists_current_campaign_no_end = artists.filter(
            project__campaign__isnull=False, campaign_end_datetime__isnull=True
        )
        artists_past_campaign = artists.filter(
            campaign_end_datetime__lt=timezone.now()
        ).order_by("-campaign_end_datetime")
        artists_no_campaign = artists.filter(project__campaign__isnull=True)
        return (
            list(artists_current_campaign)
            + list(artists_current_campaign_no_end)
            + list(artists_past_campaign)
            + list(artists_no_campaign)
        )

    def order_by_num_investors(self):
        return self.annotate(
            num_investors=models.Count(
                models.Case(
                    models.When(
                        project__campaign__investment__charge__paid=True,
                        project__campaign__investment__charge__refunded=False,
                        then="project__campaign__investment__charge__customer__user",
                    )
                ),
                distinct=True,
            )
        ).order_by("-num_investors")

    def order_by_amount_raised(self):
        return self.annotate(
            amount_raised=models.Sum(
                models.Case(
                    models.When(
                        project__campaign__investment__charge__paid=True,
                        project__campaign__investment__charge__refunded=False,
                        then=(
                            models.F("project__campaign__investment__num_shares")
                            * models.F("project__campaign__value_per_share")
                        ),
                    ),
                    default=0,
                    output_field=models.IntegerField(),
                )
            )
        ).order_by("-amount_raised")

    def order_by_valuation(self):
        return sorted(
            self, key=lambda artist: self.valuation(artist) or 0, reverse=True
        )
