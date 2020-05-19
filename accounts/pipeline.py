"""
:Created: 13 May 2016
:Author: Lucas Connors

"""
import os
from urllib.parse import urlparse

import requests
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse

from accounts.models import UserAvatar, UserAvatarImage, UserAvatarURL
from emails.messages import WelcomeEmail
from emails.models import VerifiedEmail

# https://stackoverflow.com/a/43843633/3241924
GOOGLE_OAUTH2_DEFAULT_AVATAR_URL = (
    "https://lh3.googleusercontent.com/"
    "-XdUIqdMkCWA/AAAAAAAAAAI/AAAAAAAAAAA/4252rscbv5M/photo.jpg"
)


def require_email(strategy, details, user=None, is_new=False, *args, **kwargs):
    if not details.get("email"):
        return HttpResponseRedirect(reverse("error_email_required"))


def verify_auth_operation(strategy, details, user=None, is_new=False, *args, **kwargs):
    auth_operation = kwargs["backend"].auth_operation
    if user and auth_operation == "register":
        return HttpResponseRedirect(reverse("error_account_exists"))
    elif not user and auth_operation == "login":
        return HttpResponseRedirect(reverse("error_account_does_not_exist"))


def mark_email_verified(strategy, details, user=None, is_new=False, *args, **kwargs):
    if user:
        VerifiedEmail.objects.update_or_create(
            defaults={"verified": True}, user=user, email=details["email"]
        )


def save_avatar(strategy, details, user=None, is_new=False, *args, **kwargs):
    # Skip if we don't have the user yet
    if not user:
        return

    # Get avatar from provider, skip if no avatar
    provider = kwargs["backend"].name.replace("-login", "").replace("-register", "")
    try:
        if provider == "google-oauth2":
            avatar_url = kwargs["response"]["picture"]
            is_default_avatar = avatar_url == GOOGLE_OAUTH2_DEFAULT_AVATAR_URL
        elif provider == "facebook":
            avatar = kwargs["response"]["picture"]["data"]
            avatar_url = avatar["url"]
            is_default_avatar = avatar["is_silhouette"]
        else:
            return
    except KeyError:
        return

    # Skip if the user just has the default avatar
    if is_default_avatar:
        return

    # For Google, use larger image than default
    if provider == "google-oauth2":
        avatar_url = avatar_url.replace("?sz=50", "?sz=150")

    # For Facebook, download the avatar
    img = None
    if provider == "facebook":
        response = requests.get(avatar_url)
        if not response.ok:
            return
        avatar_filename = os.path.basename(urlparse(avatar_url).path) or "avatar"
        img = ContentFile(content=response.content, name=avatar_filename)

    # Save avatar from URL
    with transaction.atomic():
        user_avatar, created = UserAvatar.objects.get_or_create(
            user=user, provider=provider
        )
        if img:
            UserAvatarImage.objects.update_or_create(
                avatar=user_avatar, defaults={"img": img}
            )
        else:
            UserAvatarURL.objects.update_or_create(
                avatar=user_avatar, defaults={"url": avatar_url}
            )

        # Update user's current avatar if none was ever set
        if created and not user.userprofile.avatar:
            user.userprofile.avatar = user_avatar
            user.userprofile.save()


def send_welcome_email(strategy, details, user=None, is_new=False, *args, **kwargs):
    if user and is_new:
        user = User.objects.get(id=user.id)
        WelcomeEmail().send(user=user)
