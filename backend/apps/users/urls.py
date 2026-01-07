"""
User URL patterns.
"""

from django.urls import path
from .views import UserRegisterView, UserMeView, UserListView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user_register'),
    path('me/', UserMeView.as_view(), name='user_me'),
    path('users/', UserListView.as_view(), name='user_list'),
]

