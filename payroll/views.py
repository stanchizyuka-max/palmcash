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
    
    from .models import PayrollPeriod, PayrollRecord
    from django.utils import timezone
    
    # Get statistics
    total_employees = Employee.objects.filter(is_active=True).count()
    total_payroll = Employee.objects.filter(is_active=True).aggregate(
        total=Sum('monthly_salary')
    )['total'] or 0
    
    # Get current month's period
    today = timezone.now().date()
    try:
        current_period = PayrollPeriod.objects.get(month=today.month, year=today.year)
        monthly_expected = current_period.total_expected
        monthly_paid = current_period.total_paid
        pending_payments = current_period.payroll_records.filter(status__in=['pending', 'partial', 'overdue']).count()
    except PayrollPeriod.DoesNotExist:
        current_period = None
        monthly_expected = 0
        monthly_paid = 0
        pending_payments = 0
    
    # Recent employees
    recent_employees = Employee.objects.filter(is_active=True).select_related('user')[:10]
    
    # Recent payments (from payroll records)
    recent_payments = PayrollRecord.objects.filter(
        status='paid'
    ).select_related('employee__user', 'processed_by').order_by('-payment_date')[:10]
    
    # Pending payments for current period
    pending_records = []
    if current_period:
        pending_records = current_period.payroll_records.filter(
            status__in=['pending', 'overdue']
        ).select_related('employee__user')[:10]
    
    context = {
        'total_employees': total_employees,
        'total_payroll': total_payroll,
        'monthly_expected': monthly_expected,
        'monthly_paid': monthly_paid,
        'monthly_payments': monthly_paid,  # Add this for template compatibility
        'pending_payments': pending_payments,
        'current_period': current_period,
        'recent_employees': recent_employees,
        'recent_payments': recent_payments,
        'pending_records': pending_records,
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



@payroll_permission_required
def payroll_periods(request):
    """List all payroll periods"""
    log_payroll_access(request.user, 'view_dashboard', 'Payroll Periods', request)
    
    from .models import PayrollPeriod
    periods = PayrollPeriod.objects.all()[:12]  # Last 12 months
    
    context = {
        'periods': periods,
    }
    
    return render(request, 'payroll/periods.html', context)


@payroll_permission_required
def period_detail(request, period_id):
    """View payroll period details and records"""
    from .models import PayrollPeriod, PayrollRecord
    
    period = get_object_or_404(PayrollPeriod, id=period_id)
    
    log_payroll_access(
        request.user,
        'view_dashboard',
        f'Payroll Period: {period}',
        request
    )
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '').strip()
    
    records = period.payroll_records.select_related('employee__user').all()
    
    if status_filter:
        records = records.filter(status=status_filter)
    
    if search:
        records = records.filter(
            Q(employee__employee_id__icontains=search) |
            Q(employee__user__first_name__icontains=search) |
            Q(employee__user__last_name__icontains=search)
        )
    
    # Count by status
    from django.db.models import Count, Sum
    status_counts = period.payroll_records.values('status').annotate(count=Count('id'))
    
    context = {
        'period': period,
        'records': records,
        'status_filter': status_filter,
        'search': search,
        'status_counts': {item['status']: item['count'] for item in status_counts},
    }
    
    return render(request, 'payroll/period_detail.html', context)


@payroll_permission_required
def process_payment(request, record_id):
    """Process payment for a payroll record"""
    from .models import PayrollRecord
    from django.utils import timezone
    
    record = get_object_or_404(PayrollRecord, id=record_id)
    
    if request.method == 'POST':
        amount_paid = request.POST.get('amount_paid')
        payment_date = request.POST.get('payment_date')
        payment_reference = request.POST.get('payment_reference', '')
        notes = request.POST.get('notes', '')
        
        try:
            amount_paid = float(amount_paid)
            
            # Update record
            record.amount_paid += amount_paid
            record.payment_date = payment_date or timezone.now().date()
            record.payment_reference = payment_reference
            record.notes = notes
            record.processed_by = request.user
            record.update_status()
            
            # Update period totals
            record.period.update_totals()
            
            # Log the action
            log_payroll_access(
                request.user,
                'create_payment',
                f'Payment: {record.employee.user.get_full_name()} - K{amount_paid:,.2f}',
                request,
                f'Processed payment for {record.period}'
            )
            
            messages.success(request, f'✓ Payment of K{amount_paid:,.2f} recorded for {record.employee.user.get_full_name()}')
            return redirect('payroll:period_detail', period_id=record.period.id)
            
        except ValueError:
            messages.error(request, 'Invalid amount entered')
    
    context = {
        'record': record,
    }
    
    return render(request, 'payroll/process_payment.html', context)
