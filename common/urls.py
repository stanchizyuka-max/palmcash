"""
URLs for common functionality
"""
from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    path('act-as-officer/<int:officer_id>/', views.start_acting_as_officer, name='start_acting_as_officer'),
    path('stop-acting-as-officer/', views.stop_acting_as_officer, name='stop_acting_as_officer'),
]
