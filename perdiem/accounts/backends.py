"""
:Created: 28 May 2016
:Author: Lucas Connors

"""

from django.conf import settings

from social.backends.facebook import FacebookOAuth2
from social.backends.google import GoogleOAuth2


class GoogleOAuth2Login(GoogleOAuth2):

    name = 'google-oauth2-login'
    auth_operation = 'login'

    def setting(self, name, default=None):
        return self.strategy.setting(name, default=default, backend=super(GoogleOAuth2Login, self))


class GoogleOAuth2Register(GoogleOAuth2):

    name = 'google-oauth2-register'
    auth_operation = 'register'

    def setting(self, name, default=None):
        return self.strategy.setting(name, default=default, backend=super(GoogleOAuth2Register, self))


class FacebookOAuth2Login(FacebookOAuth2):

    name = 'facebook-login'
    auth_operation = 'login'

    def setting(self, name, default=None):
        return self.strategy.setting(name, default=default, backend=super(FacebookOAuth2Login, self))


class FacebookOAuth2Register(FacebookOAuth2):

    name = 'facebook-register'
    auth_operation = 'register'

    def setting(self, name, default=None):
        return self.strategy.setting(name, default=default, backend=super(FacebookOAuth2Register, self))