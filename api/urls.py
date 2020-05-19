"""
:Created: 29 May 2016
:Author: Lucas Connors

"""

from django.conf.urls import url

from api.views import CoordinatesFromAddress, DeleteUpdate, PaymentCharge

urlpatterns = [
    url(r"^coordinates/?$", CoordinatesFromAddress.as_view()),
    url(
        r"^payments/charge/(?P<campaign_id>\d+)/?$",
        PaymentCharge.as_view(),
        name="pinax_stripe_charge",
    ),
    url(r"^update/(?P<update_id>\d+)/?$", DeleteUpdate.as_view()),
]
