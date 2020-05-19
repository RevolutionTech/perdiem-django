"""
:Created: 29 May 2016
:Author: Lucas Connors

"""

from unittest import mock

from geopy.exc import GeocoderTimedOut

from accounts.factories import UserFactory
from artist.factories import ArtistAdminFactory, UpdateFactory
from campaign.factories import CampaignFactory
from perdiem.tests import PerDiemTestCase


class CoordinatesFromAddressTestCase(PerDiemTestCase):

    url = "/api/coordinates/?address={address}"
    valid_url = url.format(address="Willowdale%2C+Toronto%2C+Ontario%2C+Canada")

    @mock.patch("api.views.geolocator.geocode")
    def testCoordinatesFromAddress(self, mock_geocode):
        # First the Geocoder service fails and so we return 503
        mock_geocode.side_effect = GeocoderTimedOut
        self.assertAPIResponseRenders(self.valid_url, status_code=503)

        # Then the Geocoder service kicks back online and we succeed
        mock_geocode.side_effect = None
        mock_geocode.return_value = mock.Mock(latitude=43.766751, longitude=-79.410332)
        response = self.assertAPIResponseRenders(self.valid_url)
        lat, lon = response["latitude"], response["longitude"]
        self.assertEqual(lat, 43.7668)
        self.assertEqual(lon, -79.4103)

    def testCoordinatesFromAddressRequiresAddress(self):
        for url in ["/api/coordinates/", self.url.format(address="")]:
            self.assertAPIResponseRenders(url, status_code=400)

    def testCoordinatesFromAddressFailsWithoutPermission(self):
        # Logout from being a superuser
        self.client.logout()

        # Coordinates from Address API requires permission
        # but you're not authenticated
        self.assertResponseRenders(self.valid_url, status_code=403)

        # Login as an ordinary user
        ordinary_user = UserFactory()
        self.client.login(
            username=ordinary_user.username, password=UserFactory._PASSWORD
        )

        # Coordinates from Address API requires permission
        # but you don't have the required permission
        self.assertResponseRenders(self.valid_url, status_code=403)


class PaymentChargeTestCase(PerDiemTestCase):
    @mock.patch("stripe.Charge.create")
    @mock.patch("stripe.Customer.create")
    def testUserInvests(self, mock_stripe_customer_create, mock_stripe_charge_create):
        # Mock responses from Stripe
        mock_stripe_customer_create.return_value = {
            "account_balance": 0,
            "business_vat_id": None,
            "created": 1462665000,
            "currency": None,
            "default_source": "card_2CXngrrA798I5wA01wQ74iTR",
            "delinquent": False,
            "description": None,
            "discount": None,
            "email": self.USER_EMAIL,
            "id": "cus_2Pc8xEoaTAnVKr",
            "livemode": False,
            "metadata": {},
            "object": "customer",
            "shipping": None,
            "sources": {
                "data": [
                    {
                        "address_city": None,
                        "address_country": None,
                        "address_line1": None,
                        "address_line1_check": None,
                        "address_line2": None,
                        "address_state": None,
                        "address_zip": None,
                        "address_zip_check": None,
                        "brand": "Visa",
                        "country": "US",
                        "customer": "cus_2Pc8xEoaTAnVKr",
                        "cvc_check": "pass",
                        "dynamic_last4": None,
                        "exp_month": 5,
                        "exp_year": 2019,
                        "fingerprint": "Lq9DFkUmxf7xWHkn",
                        "funding": "credit",
                        "id": "card_2CXngrrA798I5wA01wQ74iTR",
                        "last4": "4242",
                        "metadata": {},
                        "name": self.USER_EMAIL,
                        "object": "card",
                        "tokenization_method": None,
                    }
                ],
                "has_more": False,
                "object": "list",
                "total_count": 1,
                "url": "/v1/customers/cus_2Pc8xEoaTAnVKr/sources",
            },
            "subscriptions": {
                "data": [],
                "has_more": False,
                "object": "list",
                "total_count": 0,
                "url": "/v1/customers/cus_2Pc8xEoaTAnVKr/subscriptions",
            },
        }
        mock_stripe_charge_create.return_value = {
            "amount": 235,
            "amount_refunded": 0,
            "application_fee": None,
            "balance_transaction": "txn_Sazj9jMCau62PxJhOLzBXM3p",
            "captured": True,
            "created": 1462665010,
            "currency": "usd",
            "customer": "cus_2Pc8xEoaTAnVKr",
            "description": None,
            "destination": None,
            "dispute": None,
            "failure_code": None,
            "failure_message": None,
            "fraud_details": {},
            "id": "ch_Upra88VQlJJPd0JxeTM0ZvHv",
            "invoice": None,
            "livemode": False,
            "metadata": {},
            "object": "charge",
            "order": None,
            "paid": True,
            "receipt_email": None,
            "receipt_number": None,
            "refunded": False,
            "refunds": {
                "data": [],
                "has_more": False,
                "object": "list",
                "total_count": 0,
                "url": "/v1/charges/ch_Upra88VQlJJPd0JxeTM0ZvHv/refunds",
            },
            "shipping": None,
            "source": {
                "address_city": None,
                "address_country": None,
                "address_line1": None,
                "address_line1_check": None,
                "address_line2": None,
                "address_state": None,
                "address_zip": None,
                "address_zip_check": None,
                "brand": "Visa",
                "country": "US",
                "customer": "cus_2Pc8xEoaTAnVKr",
                "cvc_check": None,
                "dynamic_last4": None,
                "exp_month": 5,
                "exp_year": 2019,
                "fingerprint": "Lq9DFkUmxf7xWHkn",
                "funding": "credit",
                "id": "card_2CXngrrA798I5wA01wQ74iTR",
                "last4": "4242",
                "metadata": {},
                "name": self.USER_EMAIL,
                "object": "card",
                "tokenization_method": None,
            },
            "source_transfer": None,
            "statement_descriptor": None,
            "status": "succeeded",
        }

        # Create campaign
        campaign = CampaignFactory()

        # User sends payment to Stripe
        self.assertResponseRenders(f"/artist/{campaign.project.artist.slug}/")
        self.assertAPIResponseRenders(
            f"/api/payments/charge/{campaign.id}/",
            status_code=205,
            method="POST",
            data={"card": "tok_6WqQnRecbRRrqvrdT1XXGP1d", "num_shares": 1},
        )


class DeleteUpdateTestCase(PerDiemTestCase):

    url = "/api/update/{update_id}/"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.update = UpdateFactory()
        cls.valid_url = cls.url.format(update_id=cls.update.id)

    def testDeleteUpdate(self):
        self.assertAPIResponseRenders(self.valid_url, status_code=204, method="DELETE")

    def testDeleteUpdateRequiresValidUpdateId(self):
        self.assertResponseRenders(self.url.format(update_id=0), status_code=403)

    def testDeleteUpdateFailsWithoutPermission(self):
        # Logout from being a superuser
        self.client.logout()

        # Delete Update API requires permission
        # but you're not authenticated
        self.assertResponseRenders(self.valid_url, status_code=403, method="DELETE")

        # Login as ordinary user
        ordinary_user = UserFactory()
        self.client.login(
            username=ordinary_user.username, password=UserFactory._PASSWORD
        )

        # Delete Update API the user to be an ArtistAdmin (or superuser)
        # but you don't have access
        self.assertResponseRenders(self.valid_url, status_code=403)

    def testDeleteUpdateOnlyAllowsArtistAdminsToUpdateTheirArtists(self):
        # Logout from being a superuser
        self.client.logout()

        # Make the manager an ArtistAdmin
        manager_username = "manager"
        ArtistAdminFactory(artist=self.update.artist, user__username=manager_username)

        # Login as manager
        self.client.login(username=manager_username, password=UserFactory._PASSWORD)

        # Delete Update API allows ArtistAdmins to update
        self.assertResponseRenders(self.valid_url, status_code=204, method="DELETE")

        # Delete Update API does not allow ArtistAdmins
        # to update artists they don't belong to
        update = UpdateFactory()
        self.assertResponseRenders(
            self.url.format(update_id=update.id), status_code=403, method="DELETE"
        )
