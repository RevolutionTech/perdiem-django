import factory
from django.apps import apps as django_apps
from django.conf import settings


def userfactory_factory(apps, has_password=True):
    class UserFactory(factory.django.DjangoModelFactory):

        _PASSWORD = "abc123"

        class Meta:
            model = apps.get_model(settings.AUTH_USER_MODEL)

        username = factory.Faker("user_name")
        email = factory.LazyAttribute(lambda user: f"{user.username}@gmail.com")

        if has_password:
            password = factory.PostGenerationMethodCall("set_password", _PASSWORD)

    return UserFactory


UserFactory = userfactory_factory(apps=django_apps)


class UserAvatarFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django_apps.get_model("accounts", "UserAvatar")

    user = factory.SubFactory(UserFactory)
