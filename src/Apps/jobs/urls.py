from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('post/', views.post_job, name='post_job'),
    path('<int:pk>/edit/', views.edit_job, name='edit_job'),
    path('<int:pk>/close/', views.close_job, name='close_job'),
]