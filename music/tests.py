"""
:Created: 24 July 2016
:Author: Lucas Connors

"""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone

from campaign.models import Campaign
from music.factories import ActivityEstimateFactory, AlbumFactory, TrackFactory
from music.models import ActivityEstimate, Album
from perdiem.tests import PerDiemTestCase


class MusicModelsTestCase(TestCase):
    def testUnicodeOfAlbumIsAlbumName(self):
        album = AlbumFactory()
        self.assertEqual(str(album), album.name)

    def testAlbumTotalActivity(self):
        # Create an album
        album = AlbumFactory()

        # Verify that an album without any tracks cannot have any activity
        self.assertEqual(album.total_downloads(), 0)
        self.assertEqual(album.total_streams(), 0)

        # Create 3 tracks for the album and create an activity estimate for one stream of the album
        for _ in range(3):
            TrackFactory(album=album)
        ActivityEstimateFactory(content_object=album, total=1)

        # Verify that the one stream of the album is considered 3 events
        self.assertEqual(album.total_streams(), 3)

    def testUnicodeOfTrack(self):
        track = TrackFactory()
        self.assertEqual(
            str(track),
            "{album_name} #1: {track_name}".format(
                album_name=track.album.name, track_name=track.name
            ),
        )

    def testTrackTotalActivity(self):
        # Create ActivityEstimates
        download_activity_estimate = ActivityEstimateFactory(
            activity_type=ActivityEstimate.ACTIVITY_DOWNLOAD, total=1
        )
        track = download_activity_estimate.content_object
        ActivityEstimateFactory(
            activity_type=ActivityEstimate.ACTIVITY_STREAM,
            content_object=track,
            total=1,
        )

        # Verify that the track has one download and one stream
        self.assertEqual(track.total_downloads(), 1)
        self.assertEqual(track.total_streams(), 1)

    def testUnicodeOfActivityEstimateIsContentObject(self):
        activity_estimate = ActivityEstimateFactory()
        self.assertEqual(str(activity_estimate), str(activity_estimate.content_object))


class MusicAdminWebTestCase(PerDiemTestCase):
    def get200s(self):
        return ["/admin/music/activityestimate/daily-report/"]

    def testActivityEstimatesRequireCampaigns(self):
        album = AlbumFactory()
        response = self.assertResponseRenders(
            "/admin/music/activityestimate/add/",
            method="POST",
            data={
                "date": timezone.now().date(),
                "activity_type": ActivityEstimate.ACTIVITY_STREAM,
                "content_type": ContentType.objects.get_for_model(album).id,
                "object_id": album.id,
                "total": 10,
            },
            has_form_error=True,
        )
        self.assertIn(
            b"You cannot create activity estimates without defining the revenue percentages",
            response.content,
        )

    def testActivityEstimatesWhereAlbumDoesNotExist(self):
        invalid_album_id = Album.objects.count() + 1
        response = self.assertResponseRenders(
            "/admin/music/activityestimate/add/",
            method="POST",
            data={
                "date": timezone.now().date(),
                "activity_type": ActivityEstimate.ACTIVITY_STREAM,
                "content_type": ContentType.objects.get_for_model(Album).id,
                "object_id": invalid_album_id,
                "total": 10,
            },
            has_form_error=True,
        )
        self.assertIn(
            "The album with ID {invalid_album_id} does not exist.".format(
                invalid_album_id=invalid_album_id
            ).encode("utf-8"),
            response.content,
        )


class MusicWebTestCase(PerDiemTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.album = AlbumFactory()
        cls.artist = cls.album.project.artist

    def get200s(self):
        return [
            "/music/",
            "/artist/{artist_slug}/{album_slug}/".format(
                artist_slug=self.artist.slug, album_slug=self.album.slug
            ),
        ]
