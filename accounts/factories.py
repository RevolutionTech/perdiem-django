from django.apps import apps as django_apps
from django.conf import settings

import factory


def userfactory_factory(apps, has_password=True):
    class UserFactory(factory.DjangoModelFactory):

        _PASSWORD = 'abc123'

        class Meta:
            model = apps.get_model(settings.AUTH_USER_MODEL)

        username = factory.Faker('user_name')
        email = factory.LazyAttribute(lambda user: "{username}@gmail.com".format(username=user.username))

        if has_password:
            password = factory.PostGenerationMethodCall('set_password', _PASSWORD)

    return UserFactory


UserFactory = userfactory_factory(apps=django_apps)


class UserAvatarFactory(factory.DjangoModelFactory):

    class Meta:
        model = django_apps.get_model('accounts', 'UserAvatar')

    user = factory.SubFactory(UserFactory)
