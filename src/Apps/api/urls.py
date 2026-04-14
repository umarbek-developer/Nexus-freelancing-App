"""
URL configuration for the REST API.

All paths are mounted under /api/ in config/urls.py.
"""
from django.urls import path

from .views import (
    AcceptOfferView,
    ClientDashboardView,
    CompleteContractView,
    FreelancerDashboardView,
    ReceivedOffersView,
    RejectOfferView,
    SendOfferView,
    WalletView,
)

urlpatterns = [
    # Offers
    path('offers/',                    SendOfferView.as_view(),      name='api_send_offer'),
    path('offers/received/',           ReceivedOffersView.as_view(), name='api_received_offers'),
    path('offers/<int:pk>/accept/',    AcceptOfferView.as_view(),    name='api_accept_offer'),
    path('offers/<int:pk>/reject/',    RejectOfferView.as_view(),    name='api_reject_offer'),

    # Contracts
    path('contracts/<int:pk>/complete/', CompleteContractView.as_view(), name='api_complete_contract'),

    # Wallet
    path('wallet/', WalletView.as_view(), name='api_wallet'),

    # Dashboards
    path('dashboard/client/',      ClientDashboardView.as_view(),      name='api_client_dashboard'),
    path('dashboard/freelancer/',  FreelancerDashboardView.as_view(),  name='api_freelancer_dashboard'),
]
