"""
:Created: 29 May 2016
:Author: Lucas Connors

"""

import decimal

import stripe
from geopy.exc import GeocoderTimedOut
from pinax.stripe.actions import charges, customers, sources
from pinax.stripe.models import Card
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.forms import CoordinatesFromAddressForm
from artist.geolocator import geolocator
from artist.models import Artist, Update
from campaign.forms import PaymentChargeForm
from campaign.models import Campaign, Investment


class AddArtistPermission(permissions.DjangoModelPermissions):
    def get_required_permissions(self, method, model_cls):
        return "artist.add_artist"


class ArtistAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            update = Update.objects.select_related("artist").get(
                id=view.kwargs["update_id"]
            )
        except Update.DoesNotExist:
            return False
        return update.artist.has_permission_to_submit_update(user=request.user)


class CoordinatesFromAddress(APIView):

    permission_classes = (AddArtistPermission,)
    queryset = Artist.objects.none()

    def get(self, request, *args, **kwargs):
        # Validate request
        form = CoordinatesFromAddressForm(request.GET)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        address = form.cleaned_data["address"]

        # Return lat/lon for address
        try:
            location = geolocator.geocode(address)
        except GeocoderTimedOut:
            return Response(
                "Geocoder service currently unavailable. Please try again later.",
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {
                "latitude": float(f"{location.latitude:.4f}"),
                "longitude": float(f"{location.longitude:.4f}"),
            }
        )


class PaymentCharge(APIView):

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, campaign_id, *args, **kwargs):
        # Validate request and campaign status
        try:
            campaign = Campaign.objects.get(id=campaign_id)
        except Campaign.DoesNotExist:
            return Response(
                "Campaign with ID {campaign_id} does not exist.".format(
                    campaign_id=campaign_id
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            if not campaign.open():
                return Response(
                    "This campaign is no longer accepting investments.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        form = PaymentChargeForm(request.data, campaign=campaign)
        if not form.is_valid():
            return Response(str(form.errors), status=status.HTTP_400_BAD_REQUEST)
        d = form.cleaned_data

        # Get card and customer
        card = d["card"]
        customer = customers.get_customer_for_user(request.user)
        if not customer:
            customer = customers.create(
                request.user, card=card, plan=None, charge_immediately=False
            )
            card = Card.objects.get(customer=customer)
        else:
            # Check if we have the card the user is using
            # If we do, update it
            # If not, create it
            stripe_card = stripe.Token.retrieve(card)["card"]
            cards_with_fingerprint = Card.objects.filter(
                customer=customer, fingerprint=stripe_card["fingerprint"]
            )
            if cards_with_fingerprint.exists():
                try:
                    card = sources.update_card(
                        customer=customer,
                        source=card,
                        exp_month=stripe_card["exp_month"],
                        exp_year=stripe_card["exp_year"],
                    )
                except stripe.error.InvalidRequestError:
                    # Sometimes Stripe does not recognize the source
                    # even though we seem to have it
                    # in those cases just re-create the source
                    card = sources.create_card(customer=customer, token=card)
            else:
                card = sources.create_card(customer=customer, token=card)

        # Create charge
        num_shares = d["num_shares"]
        amount = decimal.Decimal(campaign.total(num_shares))
        try:
            charge = charges.create(
                amount=amount, customer=customer.stripe_id, source=card
            )
        except stripe.error.CardError as e:
            return Response(e.user_message, status=status.HTTP_400_BAD_REQUEST)
        Investment.objects.create(
            charge=charge, campaign=campaign, num_shares=num_shares
        )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class DeleteUpdate(APIView):

    permission_classes = (permissions.IsAuthenticated, ArtistAdminPermission)

    def delete(self, request, *args, **kwargs):
        Update.objects.get(id=self.kwargs["update_id"]).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
