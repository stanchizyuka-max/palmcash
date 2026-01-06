from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='home'),  # Alias for 'home'
    path('', views.dashboard, name='list'),  # Alias for 'list'
    path('loan-officer/', views.loan_officer_dashboard, name='loan_officer_dashboard'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Action URLs
    path('pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('collection-details/', views.collection_details, name='collection_details'),
    path('manage-officers/', views.manage_officers, name='manage_officers'),
    path('manage-branches/', views.manage_branches, name='manage_branches'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    
    # Approval URLs
    path('approval/<int:approval_id>/', views.approval_detail, name='approval_detail'),
    path('approval/<int:approval_id>/approve/', views.approval_approve, name='approval_approve'),
    path('approval/<int:approval_id>/reject/', views.approval_reject, name='approval_reject'),
    path('approval-history/', views.approval_history, name='approval_history'),
    
    # Expense URLs
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/report/', views.expense_report, name='expense_report'),
    
    # Fund URLs
    path('funds/transfer/', views.fund_transfer_create, name='fund_transfer_create'),
    path('funds/deposit/', views.fund_deposit_create, name='fund_deposit_create'),
    path('funds/history/', views.fund_history, name='fund_history'),
    
    # User and Branch Management URLs
    path('users/create/', views.user_create, name='user_create'),
    path('branches/create/', views.branch_create, name='branch_create'),
    
    # Admin Branch Management URLs
    path('admin/branches/', views.admin_branches_list, name='admin_branches_list'),
    path('admin/branches/<int:branch_id>/', views.admin_branch_detail, name='admin_branch_detail'),
    path('admin/branches/create/', views.admin_branch_create, name='admin_branch_create'),
    path('admin/branches/<int:branch_id>/edit/', views.admin_branch_edit, name='admin_branch_edit'),
    path('admin/branches/<int:branch_id>/deactivate/', views.admin_branch_deactivate, name='admin_branch_deactivate'),
    
    # Admin Officer Transfer URLs
    path('admin/officers/', views.admin_officers_list, name='admin_officers_list'),
    path('admin/officers/<int:officer_id>/transfer/', views.admin_officer_transfer, name='admin_officer_transfer'),
    path('admin/transfers/history/', views.admin_transfer_history, name='admin_transfer_history'),
    
    # Admin Client Transfer URLs
    path('admin/clients/transfer/', views.admin_client_transfer, name='admin_client_transfer'),
    path('admin/clients/transfer/history/', views.admin_client_transfer_history, name='admin_client_transfer_history'),
    
    # Admin Group Assignment Override URLs
    path('admin/assignments/override/', views.admin_override_assignment, name='admin_override_assignment'),
    
    # Admin High-Value Loan Approval URLs
    path('admin/approvals/pending/', views.admin_pending_approvals, name='admin_pending_approvals'),
    path('admin/approvals/loan/<int:loan_id>/', views.admin_loan_approval_detail, name='admin_loan_approval_detail'),
    path('admin/approvals/loan/<int:loan_id>/approve/', views.admin_loan_approve, name='admin_loan_approve'),
    path('admin/approvals/loan/<int:loan_id>/reject/', views.admin_loan_reject, name='admin_loan_reject'),
    
    # Admin Company-Wide Loan Viewing URLs
    path('admin/loans/', views.admin_all_loans, name='admin_all_loans'),
    path('admin/loans/<int:loan_id>/', views.admin_loan_detail, name='admin_loan_detail'),
    path('admin/loans/statistics/', views.admin_loan_statistics, name='admin_loan_statistics'),
]
