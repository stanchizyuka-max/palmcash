from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Group management
    path('groups/', views.GroupListView.as_view(), name='group_list'),
    path('groups/create/', views.GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:pk>/edit/', views.GroupUpdateView.as_view(), name='group_edit'),
    path('groups/<int:pk>/add-member/', views.AddMemberView.as_view(), name='add_member'),
    path('groups/<int:pk>/remove-member/<int:membership_id>/', views.RemoveMemberView.as_view(), name='remove_member'),
    path('groups/<int:pk>/assign-officer/', views.AssignOfficerToGroupView.as_view(), name='assign_officer'),
    
    # Client assignment
    path('clients/<int:client_id>/assign-officer/', views.AssignClientToOfficerView.as_view(), name='assign_client'),
    path('clients/<int:client_id>/unassign-officer/', views.UnassignClientFromOfficerView.as_view(), name='unassign_client'),
    
    # Officer clients
    path('officers/<int:officer_id>/clients/', views.OfficerClientsListView.as_view(), name='officer_clients'),
    
    # Officer workload
    path('officers/workload/', views.OfficerWorkloadView.as_view(), name='officer_workload'),
    path('officers/<int:pk>/workload-detail/', views.OfficerWorkloadDetailView.as_view(), name='officer_workload_detail'),
    path('officers/<int:officer_id>/update-capacity/', views.UpdateOfficerCapacityView.as_view(), name='update_officer_capacity'),
]
