from django.urls import path
from . import views

urlpatterns = [
    path('submit/<int:job_pk>/', views.submit_proposal, name='submit_proposal'),
    path('my/', views.my_proposals, name='my_proposals'),
    path('job/<int:job_pk>/', views.view_proposals, name='view_proposals'),
    path('<int:pk>/accept/', views.accept_proposal, name='accept_proposal'),
    path('<int:pk>/reject/', views.reject_proposal, name='reject_proposal'),
]