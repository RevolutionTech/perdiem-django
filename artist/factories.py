import factory
from django.apps import apps as django_apps
from django.utils.text import slugify

from accounts.factories import UserFactory


def artistfactory_factory(apps):
    class ArtistFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = apps.get_model("artist", "Artist")

        name = factory.Faker("user_name")
        slug = factory.LazyAttribute(lambda artist: slugify(artist.name))

        # Willowdale, Toronto, Ontario, Canada
        lat = 43.7689
        lon = -79.4138

    return ArtistFactory


def updatefactory_factory(apps):
    class UpdateFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = apps.get_model("artist", "Update")

        artist = factory.SubFactory(artistfactory_factory(apps=apps))

    return UpdateFactory


ArtistFactory = artistfactory_factory(apps=django_apps)
UpdateFactory = updatefactory_factory(apps=django_apps)


class GenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django_apps.get_model("artist", "Genre")


class ArtistAdminFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django_apps.get_model("artist", "ArtistAdmin")

    artist = factory.SubFactory(ArtistFactory)
    user = factory.SubFactory(UserFactory)
