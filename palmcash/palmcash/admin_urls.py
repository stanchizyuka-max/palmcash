"""
URL configuration for admin authentication views.
"""
from django.urls import path
from . import admin_auth

app_name = 'admin_auth'

urlpatterns = [
    path('manager-login/', admin_auth.manager_admin_login, name='manager_login'),
    path('access-denied/', admin_auth.admin_access_denied, name='access_denied'),
]
