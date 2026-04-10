from django.urls import path
from . import views

urlpatterns = [
    path('', views.browse_freelancers, name='browse_freelancers'),
    path('<int:pk>/', views.freelancer_profile, name='freelancer_profile'),
]