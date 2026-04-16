from django.urls import path
from . import views

app_name = 'securities'

urlpatterns = [
    path('', views.securities_summary, name='summary'),
    path('branches/', views.securities_branches, name='branches'),
    path('branch/<int:branch_id>/officers/', views.securities_officers, name='branch_officers'),
    path('officer/<int:officer_id>/', views.officer_groups, name='officer_groups'),
    path('group/<int:group_id>/', views.group_clients, name='group_clients'),
    path('client/<int:client_id>/', views.client_detail, name='client_detail'),
]
