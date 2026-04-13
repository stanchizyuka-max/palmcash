from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date
from .decorators import payroll_permission_required
from .models import Employee, SalaryRecord, PayrollPayment, PayrollAuditLog
from accounts.models import User


def log_payroll_access(user, action, target, request, details=''):
    """Helper function to log payroll access"""
    ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
    PayrollAuditLog.objects.create(
        user=user,
        action=action,
        target=target,
        ip_address=ip_address,
        details=details
    )


@payroll_permission_required
def payroll_dashboard(request):
    """Main payroll dashboard"""
    # Log access
    log_payroll_access(request.user, 'view_dashboard', 'Payroll Dashboard', request)
    
    # Get statistics
    total_employees = Employee.objects.filter(is_active=True).count()
    total_payroll = SalaryRecord.objects.aggregate(
        total=Sum('base_salary')
    )['total'] or 0
    
    # This month's payments
    today = date.today()
    month_start = today.replace(day=1)
    monthly_payments = PayrollPayment.objects.filter(
        payment_date__gte=month_start,
        status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    pending_payments = PayrollPayment.objects.filter(status='pending').count()
    
    # Recent employees
    recent_employees = Employee.objects.filter(is_active=True).select_related('user')[:10]
    
    # Recent payments
    recent_payments = PayrollPayment.objects.select_related(
        'employee__user', 'processed_by'
    ).order_by('-payment_date')[:10]
    
    context = {
        'total_employees': total_employees,
        'total_payroll': total_payroll,
        'monthly_payments': monthly_payments,
        'pending_payments': pending_payments,
        'recent_employees': recent_employees,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'payroll/dashboard.html', context)


@payroll_permission_required
def employee_list(request):
    """List all employees"""
    log_payroll_access(request.user, 'view_employee', 'Employee List', request)
    
    search = request.GET.get('search', '').strip()
    branch = request.GET.get('branch', '')
    
    employees = Employee.objects.filter(is_active=True).select_related('user')
    
    if search:
        employees = employees.filter(
            Q(employee_id__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(position__icontains=search)
        )
    
    if branch:
        employees = employees.filter(branch=branch)
    
    # Get unique branches
    branches = Employee.objects.exclude(branch='').values_list('branch', flat=True).distinct().order_by('branch')
    
    context = {
        'employees': employees,
        'branches': branches,
        'search': search,
        'branch': branch,
    }
    
    return render(request, 'payroll/employee_list.html', context)


@payroll_permission_required
def salary_detail(request, employee_id):
    """View salary details for an employee"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    log_payroll_access(
        request.user, 
        'view_salary', 
        f'Employee: {employee.user.get_full_name()}',
        request,
        f'Viewed salary for employee ID {employee.employee_id}'
    )
    
    salary_records = SalaryRecord.objects.filter(employee=employee).select_related('created_by')
    payments = PayrollPayment.objects.filter(employee=employee).select_related('processed_by')
    
    # Calculate totals
    total_paid = payments.filter(status='paid').aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    
    context = {
        'employee': employee,
        'salary_records': salary_records,
        'payments': payments,
        'total_paid': total_paid,
    }
    
    return render(request, 'payroll/salary_detail.html', context)


@payroll_permission_required
def payment_history(request):
    """View payment history"""
    log_payroll_access(request.user, 'view_dashboard', 'Payment History', request)
    
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '').strip()
    
    payments = PayrollPayment.objects.select_related(
        'employee__user', 'processed_by'
    ).order_by('-payment_date')
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    if search:
        payments = payments.filter(
            Q(employee__employee_id__icontains=search) |
            Q(employee__user__first_name__icontains=search) |
            Q(employee__user__last_name__icontains=search) |
            Q(reference_number__icontains=search)
        )
    
    context = {
        'payments': payments,
        'status_filter': status_filter,
        'search': search,
    }
    
    return render(request, 'payroll/payment_history.html', context)


@payroll_permission_required
def audit_logs(request):
    """View audit logs"""
    logs = PayrollAuditLog.objects.select_related('user').order_by('-timestamp')[:100]
    
    context = {
        'logs': logs,
    }
    
    return render(request, 'payroll/audit_logs.html', context)
