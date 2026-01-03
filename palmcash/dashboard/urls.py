from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_redirect, name='home'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin'),
    path('manager/', views.ManagerDashboardView.as_view(), name='manager'),
    path('officer/', views.LoanOfficerDashboardView.as_view(), name='officer'),
    path('borrower/', views.BorrowerDashboardView.as_view(), name='borrower'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    
    # Admin Management Pages
    path('admin/users/', views.ManageUsersView.as_view(), name='manage_users'),
    path('admin/loans/', views.ManageLoansView.as_view(), name='manage_loans'),
    path('admin/groups/', views.GroupsPermissionsView.as_view(), name='groups_permissions'),
    path('admin/groups/add/', views.AddGroupView.as_view(), name='add_group'),
    path('admin/groups/manage/', views.ManageGroupsView.as_view(), name='manage_groups'),
    path('admin/reports/', views.SystemReportsView.as_view(), name='system_reports'),
]