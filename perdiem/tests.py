"""
:Created: 5 March 2016
:Author: Lucas Connors

"""

from django.apps import apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, override_settings
from pigeon.test import RenderTestCase

from accounts.factories import UserFactory


@override_settings(PASSWORD_HASHERS=("django.contrib.auth.hashers.MD5PasswordHasher",))
class PerDiemTestCase(RenderTestCase):

    USER_USERNAME = "jsmith"
    USER_EMAIL = "jsmith@example.com"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory(
            username=cls.USER_USERNAME,
            email=cls.USER_EMAIL,
            is_staff=True,
            is_superuser=True,
        )

    def setUp(self):
        self.client.login(username=self.USER_USERNAME, password=UserFactory._PASSWORD)


class MigrationTestCase(TestCase):
    """
    Ref: https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
    """

    migrate_from = None
    migrate_to = None

    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name

    def setUp(self):
        # Verify that migration_from and migration_to are defined
        assertion_error_message = (
            "MigrationTestCase '{test_case_name}' must define migrate_from and migrate_to properties."
        ).format(test_case_name=type(self).__name__)
        assert self.migrate_from and self.migrate_to, assertion_error_message

        # Init MigrationExecutor
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to old migration
        executor.migrate(self.migrate_from)

        # Create model instances before migration runs
        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass


class HealthCheckWebTestCase(RenderTestCase):
    def get200s(self):
        return ["/health-check/"]


class ExtrasWebTestCase(RenderTestCase):
    def get200s(self):
        return [
            "/faq/",
            "/trust/",
            "/terms/",
            "/privacy/",
            "/contact/",
            "/artist-resources/",
            "/investor-resources/",
        ]

    def testContact(self):
        # Login as user
        user = UserFactory()
        self.client.login(username=user.username, password=UserFactory._PASSWORD)

        # Verify that contact form submits successfully
        self.assertResponseRedirects(
            "/contact/",
            "/contact/thanks",
            method="POST",
            data={
                "inquiry": "general_inquiry",
                "email": "msmith@example.com",
                "message": "Hello World!",
            },
        )
