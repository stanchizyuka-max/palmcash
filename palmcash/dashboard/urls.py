from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard routes
    path('', views.dashboard, name='dashboard'),
    path('loan-officer/', views.loan_officer_dashboard, name='loan_officer_dashboard'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/document-verification/', views.manager_document_verification, name='manager_document_verification'),
    path('loan-officer/document-verification/', views.loan_officer_document_verification, name='loan_officer_document_verification'),
    
    # Action URLs
    path('pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('approved-security-deposits/', views.approved_security_deposits, name='approved_security_deposits'),
    path('collection-details/', views.collection_details, name='collection_details'),
    
    # Approval URLs
    path('approval/<int:approval_id>/', views.approval_detail, name='approval_detail'),
    path('approval/<int:approval_id>/approve/', views.approval_approve, name='approval_approve'),
    path('approval/<int:approval_id>/reject/', views.approval_reject, name='approval_reject'),
    path('approval-history/', views.approval_history, name='approval_history'),
    
    # Manager Loan Approval URLs
    path('manager/loan/<int:loan_id>/approve/', views.manager_loan_approval_detail, name='manager_loan_approval_detail'),
    path('manager/loan/<int:loan_id>/approve-action/', views.manager_loan_approve, name='manager_loan_approve'),
    path('manager/loan/<int:loan_id>/reject/', views.manager_loan_reject, name='manager_loan_reject'),
    
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
    path('manage-officers/', views.manage_officers, name='manage_officers'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    
    # Admin Branch Management URLs
    path('admin/branches/', views.admin_branches_list, name='admin_branches_list'),
    path('admin/branches/create/', views.admin_branch_create, name='admin_branch_create'),
    path('admin/branches/<int:branch_id>/', views.admin_branch_detail, name='admin_branch_detail'),
    path('admin/branches/<int:branch_id>/edit/', views.admin_branch_edit, name='admin_branch_edit'),
    path('admin/branches/<int:branch_id>/deactivate/', views.admin_branch_deactivate, name='admin_branch_deactivate'),
    
    # Admin Officer Management URLs
    path('admin/officers/', views.admin_officers_list, name='admin_officers_list'),
    path('admin/officers/transfer/', views.admin_officer_transfer, name='admin_officer_transfer'),
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
    
    # Admin Management URLs (aliases for dashboard links)
    path('manage-loans/', views.admin_all_loans, name='manage_loans'),
    path('groups-permissions/', views.groups_permissions, name='groups_permissions'),
    path('system-reports/', views.system_reports, name='system_reports'),
    path('analytics/', views.analytics, name='analytics'),
]
