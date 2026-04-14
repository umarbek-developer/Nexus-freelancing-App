from django.urls import path
from . import views

urlpatterns = [
    path('', views.browse_freelancers, name='browse_freelancers'),
    path('<int:pk>/', views.freelancer_profile, name='freelancer_profile'),
    # #10: Portfolio management
    path('portfolio/add/', views.portfolio_add, name='portfolio_add'),
    path('portfolio/<int:pk>/delete/', views.portfolio_delete, name='portfolio_delete'),
]