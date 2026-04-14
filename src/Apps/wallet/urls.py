from django.urls import path
from . import views

urlpatterns = [
    path('',          views.wallet_overview,   name='wallet_overview'),
    path('withdraw/', views.withdrawal_request, name='withdrawal_request'),
]
