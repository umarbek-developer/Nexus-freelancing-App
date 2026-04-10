from django.urls import path
from . import views

urlpatterns = [
    path('leave/<int:contract_pk>/', views.leave_review, name='leave_review'),
]