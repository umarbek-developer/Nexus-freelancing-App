from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_contracts, name='my_contracts'),
    path('<int:pk>/', views.contract_detail, name='contract_detail'),
    path('<int:pk>/complete/', views.complete_contract, name='complete_contract'),
    path('<int:pk>/dispute/', views.open_dispute, name='open_dispute'),   # #14
]