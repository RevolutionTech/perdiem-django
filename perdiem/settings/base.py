"""
:Created: 26 July 2015
:Author: Lucas Connors

"""

import os

from cbsettings import DjangoDefaults
import requests


def aws_s3_bucket_url(settings_class, bucket_name_settings):
    bucket_name = getattr(settings_class, bucket_name_settings, "")
    if bucket_name:
        return f"https://{bucket_name}.s3.amazonaws.com"
    return ""


class BaseSettings(DjangoDefaults):

    BASE_DIR = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    SECRET_KEY = os.environ["PERDIEM_SECRET_KEY"]
    DEBUG = True
    ACCEPTABLE_HOSTS = ["localhost", "127.0.0.1", ".investperdiem.com"]

    @property
    def ALLOWED_HOSTS(self):
        # Get cached ALLOWED_HOSTS setting, if available
        if hasattr(self, "_ALLOWED_HOSTS"):
            return self._ALLOWED_HOSTS

        # When DEBUG == True, ALLOWED_HOSTS is just ACCEPTABLE_HOSTS
        if self.DEBUG:
            self._ALLOWED_HOSTS = self.ACCEPTABLE_HOSTS
            return self._ALLOWED_HOSTS

        # Otherwise, add EC2 IP to ACCEPTABLE_HOSTS
        hosts = self.ACCEPTABLE_HOSTS
        try:
            ec2_ip = requests.get(
                "http://169.254.169.254/latest/meta-data/local-ipv4", timeout=0.01
            ).text
        except requests.exceptions.RequestException:
            pass
        else:
            hosts.append(ec2_ip)
            self._ALLOWED_HOSTS = hosts
        return hosts

    # Application definition
    INSTALLED_APPS = (
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "whitenoise.runserver_nostatic",
        "django.contrib.staticfiles",
        "django.contrib.sites",
        "django.contrib.humanize",
        "sorl.thumbnail",
        "django_s3_storage",
        "rest_framework",
        "social_django",
        "pinax.stripe",
        "markdown_deux",
        "pagedown",
        "accounts.apps.AccountsConfig",
        "api.apps.ApiConfig",
        "artist.apps.ArtistConfig",
        "campaign.apps.CampaignConfig",
        "emails.apps.EmailsConfig",
        "music.apps.MusicConfig",
    )
    MIDDLEWARE = [
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "social_django.middleware.SocialAuthExceptionMiddleware",
        "accounts.middleware.LoginFormMiddleware",
    ]
    ROOT_URLCONF = "perdiem.urls"
    SITE_ID = 1

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [os.path.join(BASE_DIR, "templates")],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                    "social_django.context_processors.backends",
                    "social_django.context_processors.login_redirect",
                    "perdiem.context_processors.request",
                    "accounts.context_processors.keys",
                    "accounts.context_processors.profile",
                ]
            },
        }
    ]
    WSGI_APPLICATION = "perdiem.wsgi.application"

    # Cache and Database
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
            "LOCATION": "127.0.0.1:11211",
        }
    }
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ["PERDIEM_DB_NAME"],
            "USER": os.environ["PERDIEM_DB_USER"],
            "PASSWORD": os.environ["PERDIEM_DB_PASSWORD"],
            "HOST": os.environ["PERDIEM_DB_HOST"],
            "PORT": "5432",
        }
    }

    # Internationalization
    TIME_ZONE = "UTC"
    USE_L10N = True
    USE_TZ = True

    # Static files (CSS, JavaScript, Images)
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
    AWS_S3_KEY_PREFIX = "media"
    AWS_S3_KEY_PREFIX_STATIC = "static"
    AWS_S3_BUCKET_AUTH = False
    AWS_S3_MAX_AGE_SECONDS = 60 * 60 * 24 * 365  # 1 year
    MAXIMUM_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB

    @property
    def MEDIA_URL(self):
        return "{aws_s3}/{media}/".format(
            aws_s3=aws_s3_bucket_url(self, "AWS_S3_BUCKET_NAME"),
            media=self.AWS_S3_KEY_PREFIX,
        )

    @property
    def STATIC_URL(self):
        return "{aws_s3}/{static}/".format(
            aws_s3=aws_s3_bucket_url(self, "AWS_S3_BUCKET_NAME_STATIC"),
            static=self.AWS_S3_KEY_PREFIX_STATIC,
        )

    # Markdown
    MARKDOWN_DEUX_STYLES = {
        "default": {"extras": {"code-friendly": None}, "safe_mode": True},
        "trusted": {
            "extras": {"code-friendly": None},
            "safe_mode": False,  # Allow raw HTML
        },
    }

    # Authentication
    AUTHENTICATION_BACKENDS = (
        "accounts.backends.GoogleOAuth2Login",
        "accounts.backends.GoogleOAuth2Register",
        "accounts.backends.FacebookOAuth2Login",
        "accounts.backends.FacebookOAuth2Register",
        "django.contrib.auth.backends.ModelBackend",
    )
    SOCIAL_AUTH_PIPELINE = (
        "social_core.pipeline.social_auth.social_details",
        "social_core.pipeline.social_auth.social_uid",
        "social_core.pipeline.social_auth.auth_allowed",
        "social_core.pipeline.social_auth.social_user",
        "social_core.pipeline.user.get_username",
        "social_core.pipeline.social_auth.associate_by_email",
        "accounts.pipeline.require_email",
        "accounts.pipeline.verify_auth_operation",
        "social_core.pipeline.user.create_user",
        "accounts.pipeline.mark_email_verified",
        "accounts.pipeline.save_avatar",
        "social_core.pipeline.social_auth.associate_user",
        "social_core.pipeline.social_auth.load_extra_data",
        "social_core.pipeline.user.user_details",
        "accounts.pipeline.send_welcome_email",
    )
    SOCIAL_AUTH_LOGIN_ERROR_URL = "/"
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ["PERDIEM_GOOGLE_OAUTH2_KEY"]
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ["PERDIEM_GOOGLE_OAUTH2_SECRET"]
    SOCIAL_AUTH_FACEBOOK_KEY = os.environ["PERDIEM_FACEBOOK_KEY"]
    SOCIAL_AUTH_FACEBOOK_SECRET = os.environ["PERDIEM_FACEBOOK_SECRET"]
    SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
    SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
        "fields": ", ".join(["id", "name", "email", "picture.width(150)"])
    }
    LOGIN_URL = "/"
    LOGIN_REDIRECT_URL = "/profile/"

    # Email
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = "/tmp/perdiem/email"
    TEMPLATED_EMAIL_TEMPLATE_DIR = "email/"
    DEFAULT_FROM_EMAIL = "PerDiem <noreply@investperdiem.com>"

    # Stripe
    PINAX_STRIPE_PUBLIC_KEY = os.environ["PERDIEM_STRIPE_PUBLIC_KEY"]
    PINAX_STRIPE_SECRET_KEY = os.environ["PERDIEM_STRIPE_SECRET_KEY"]
    PINAX_STRIPE_SEND_EMAIL_RECEIPTS = False
    PERDIEM_PERCENTAGE = 0.1  # 10%
    STRIPE_PERCENTAGE = 0.029  # 2.9%
    STRIPE_FLAT_FEE = 0.3  # $0.30
    DEFAULT_MIN_PURCHASE = 1  # $1

    # MailChimp
    MAILCHIMP_API_KEY = os.environ["PERDIEM_MAILCHIMP_API_KEY"]
    MAILCHIMP_LIST_ID = os.environ["PERDIEM_MAILCHIMP_LIST_ID"]

    # Analytics
    GA_TRACKING_CODE = os.environ.get("PERDIEM_GA_TRACKING_CODE")
    JACO_API_KEY = os.environ.get("PERDIEM_JACO_API_KEY")
    ITUNES_AFFILIATE_TOKEN = os.environ.get("PERDIEM_ITUNES_AFFILIATE_TOKEN")
