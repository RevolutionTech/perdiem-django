import factory
from django.apps import apps
from django.utils.text import slugify

from campaign.factories import ProjectFactory
from music.models import ActivityEstimate as ActivityEstimateConst


class AlbumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = apps.get_model("music", "Album")

    project = factory.SubFactory(ProjectFactory)
    name = factory.Sequence(lambda n: f"Album #{n}")
    slug = factory.LazyAttribute(lambda album: slugify(album.name))


class TrackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = apps.get_model("music", "Track")

    album = factory.SubFactory(AlbumFactory)
    track_number = factory.LazyAttribute(
        lambda track: track.album.track_set.count() + 1
    )


class ActivityEstimateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = apps.get_model("music", "ActivityEstimate")

    activity_type = ActivityEstimateConst.ACTIVITY_STREAM
    content_object = factory.SubFactory(TrackFactory)
    total = 500
