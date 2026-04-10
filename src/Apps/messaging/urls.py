from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('conversation/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('start/<int:user_pk>/', views.start_conversation, name='start_conversation'),
]