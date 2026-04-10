from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/client/', views.client_dashboard, name='client_dashboard'),
    path('dashboard/freelancer/', views.freelancer_dashboard, name='freelancer_dashboard'),
    path('settings/', views.profile_settings, name='profile_settings'),
]