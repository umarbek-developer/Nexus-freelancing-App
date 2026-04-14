from django.urls import path
from . import views

urlpatterns = [
    # Role selection
    path('register/',             views.register_role_select, name='register'),
    path('register/client/',      views.register_client,      name='register_client'),
    path('register/freelancer/',  views.register_freelancer,  name='register_freelancer'),

    # Login (universal + role-specific)
    path('login/',                views.login_view,           name='login'),
    path('login/client/',         views.login_client,         name='login_client'),
    path('login/freelancer/',     views.login_freelancer,     name='login_freelancer'),

    path('logout/',               views.logout_view,          name='logout'),
    path('dashboard/',            views.dashboard,            name='dashboard'),
    path('dashboard/client/',     views.client_dashboard,     name='client_dashboard'),
    path('dashboard/freelancer/', views.freelancer_dashboard, name='freelancer_dashboard'),
    path('settings/',             views.profile_settings,     name='profile_settings'),
]
