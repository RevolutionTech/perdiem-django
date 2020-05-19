"""
:Created: 12 May 2016
:Author: Lucas Connors

"""

from django.contrib import admin
from django.contrib.sites.models import Site
from social_django.models import Association, Nonce, UserSocialAuth

# Unregister Site and Python Social Auth models from admin
admin.site.unregister(Site)
for python_social_auth_model in [Association, Nonce, UserSocialAuth]:
    admin.site.unregister(python_social_auth_model)
