from django.urls import path
from . import views, admin_views

app_name = 'payroll'

urlpatterns = [
    # Main payroll views
    path('', views.payroll_dashboard, name='dashboard'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:employee_id>/', views.salary_detail, name='salary_detail'),
    path('payments/', views.payment_history, name='payment_history'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    
    # Payroll periods and records
    path('periods/', views.payroll_periods, name='periods'),
    path('periods/<int:period_id>/', views.period_detail, name='period_detail'),
    path('records/<int:record_id>/pay/', views.process_payment, name='process_payment'),
    
    # Admin management
    path('admin/manage-access/', admin_views.manage_payroll_access, name='manage_access'),
]
