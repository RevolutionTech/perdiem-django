"""
:Created: 5 April 2016
:Author: Lucas Connors

"""

from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, FormView

from accounts.forms import (
    ContactForm,
    EditAvatarForm,
    EditNameForm,
    EmailPreferencesForm,
    RegisterAccountForm,
)
from accounts.models import UserAvatar, UserAvatarImage
from artist.models import Artist, Update
from emails.messages import ContactEmail, EmailVerificationEmail, WelcomeEmail
from emails.models import EmailSubscription, VerifiedEmail
from music.models import Album
from perdiem.views import ConstituentFormView, MultipleFormView


class RegisterAccountView(CreateView):

    template_name = "registration/register.html"
    form_class = RegisterAccountForm

    def get_success_url(self):
        return self.request.GET.get("next") or reverse("profile")

    def form_valid(self, form):
        valid = super().form_valid(form)

        # Login the newly-registered user
        d = form.cleaned_data
        username, password = d["username"], d["password1"]
        user = authenticate(username=username, password=password)
        if user:
            login(self.request, user)

        # Create the user's newsletter subscription (if applicable)
        if d["subscribe_news"]:
            EmailSubscription.objects.create(
                user=user, subscription=EmailSubscription.SUBSCRIPTION_NEWS
            )

        # Send Welcome email
        VerifiedEmail.objects.create(user=user, email=user.email)
        WelcomeEmail().send(user=user)

        return valid


class VerifyEmailView(TemplateView):

    template_name = "registration/verify_email.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        verified_email = get_object_or_404(
            VerifiedEmail, user__id=kwargs["user_id"], code=kwargs["code"]
        )
        verified_email.verified = True
        verified_email.save()
        context["verified_email"] = verified_email

        return context


class EditNameFormView(ConstituentFormView):

    form_class = EditNameForm
    provide_user = True

    def get_initial(self):
        user = self.request.user
        return {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "invest_anonymously": user.userprofile.invest_anonymously,
        }

    def form_valid(self, form):
        user = self.request.user
        d = form.cleaned_data

        # Update username and name
        user.username = d["username"]
        user.first_name = d["first_name"]
        user.last_name = d["last_name"]
        user.save()

        # Update anonymity
        user.userprofile.invest_anonymously = d["invest_anonymously"]
        user.userprofile.save()


class EditAvatarFormView(ConstituentFormView):

    form_class = EditAvatarForm
    provide_user = True
    includes_files = True

    def get_initial(self):
        user_profile = self.request.user.userprofile
        return {"avatar": user_profile.avatar.id if user_profile.avatar else ""}

    def form_valid(self, form):
        user = self.request.user
        d = form.cleaned_data

        # Upload a custom avatar, if provided
        user_avatar = d["avatar"]
        custom_avatar = d["custom_avatar"]
        if custom_avatar:
            user_avatar, _ = UserAvatar.objects.get_or_create(
                user=user, provider=UserAvatar.PROVIDER_PERDIEM
            )
            UserAvatarImage.objects.update_or_create(
                avatar=user_avatar, defaults={"img": custom_avatar}
            )

        # Update user's avatar
        user.userprofile.avatar = user_avatar
        user.userprofile.save()


class ChangePasswordFormView(ConstituentFormView):

    form_class = PasswordChangeForm
    provide_user = True

    def form_valid(self, form):
        user = self.request.user
        d = form.cleaned_data

        # Update user's password
        user.set_password(d["new_password1"])
        user.save()
        update_session_auth_hash(self.request, user)


class EmailPreferencesFormView(ConstituentFormView):

    form_class = EmailPreferencesForm
    provide_user = True

    def get_initial(self):
        initial = {"email": self.request.user.email}
        for subscription_type, _ in EmailSubscription.SUBSCRIPTION_CHOICES:
            subscribed = EmailSubscription.objects.is_subscribed(
                user=self.request.user, subscription_type=subscription_type
            )
            initial[f"subscription_{subscription_type.lower()}"] = subscribed
        return initial

    def form_valid(self, form):
        user = self.request.user
        d = form.cleaned_data

        # Update user's email subscriptions
        email_subscriptions = {
            k: v for k, v in d.items() if k.startswith("subscription_")
        }
        for subscription_type, is_subscribed in email_subscriptions.items():
            EmailSubscription.objects.update_or_create(
                user=user,
                subscription=getattr(EmailSubscription, subscription_type.upper()),
                defaults={"subscribed": is_subscribed},
            )

        # Update user's email address
        if d["email"] != user.email:
            user.email = d["email"]
            user.save()
            if not VerifiedEmail.objects.is_current_email_verified(user):
                EmailVerificationEmail().send(user=user)


class SettingsView(LoginRequiredMixin, MultipleFormView):

    template_name = "registration/settings.html"
    constituent_form_views = {
        "edit_name": EditNameFormView,
        "edit_avatar": EditAvatarFormView,
        "change_password": ChangePasswordFormView,
        "email_preferences": EmailPreferencesFormView,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Update context with available avatars
        user = self.request.user
        user_avatars = UserAvatar.objects.filter(user=user)
        avatars = {"Default": user.userprofile.default_avatar_url()}
        avatars.update(
            {
                avatar.get_provider_display(): avatar.avatar_url()
                for avatar in user_avatars
            }
        )
        context["avatars"] = avatars

        return context


class ProfileView(LoginRequiredMixin, TemplateView):

    template_name = "registration/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Update context with profile information
        context.update(self.request.user.userprofile.profile_context())
        context["albums"] = Album.objects.filter(
            project__campaign__in=context["campaigns"]
        ).distinct()
        context["updates"] = Update.objects.filter(
            artist__in=context["artists"]
        ).order_by("-created_datetime")

        return context


class PublicProfileView(TemplateView):

    template_name = "registration/public_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = get_object_or_404(User, username=kwargs["username"])
        if profile_user.userprofile.invest_anonymously:
            raise Http404("No User matches the given query.")
        context.update(
            {
                "profile_user": profile_user,
                "profile": profile_user.userprofile.profile_context(),
            }
        )
        return context


class ContactFormView(FormView):

    template_name = "registration/contact.html"
    form_class = ContactForm

    def get_success_url(self):
        return reverse("contact_thanks")

    def get_initial(self):
        initial = super().get_initial()

        user = self.request.user
        if user.is_authenticated:
            initial["email"] = user.email
            initial["first_name"] = user.first_name
            initial["last_name"] = user.last_name

        inquiry = self.request.GET.get("inquiry")
        if inquiry:
            initial["inquiry"] = inquiry

        return initial

    def form_valid(self, form):
        # Add user_id to context, if available
        context = form.cleaned_data
        user = self.request.user
        if user.is_authenticated:
            context["user_id"] = user.id

        # Send contact email
        ContactEmail().send_to_email(email="support@investperdiem.com", context=context)

        return super().form_valid(form)


def redirect_to_profile(request, slug):
    # Try matching the slug to an artists
    try:
        artist = Artist.objects.get(slug=slug)
    except Artist.DoesNotExist:
        pass
    else:
        return HttpResponseRedirect(reverse("artist", kwargs={"slug": artist.slug}))

    # Try matching the slug to a public profile
    try:
        user = User.objects.exclude(userprofile__invest_anonymously=True).get(
            username=slug
        )
    except User.DoesNotExist:
        raise Http404
    else:
        return HttpResponseRedirect(
            reverse("public_profile", kwargs={"username": user.username})
        )
