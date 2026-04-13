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


@payroll_permission_required
def edit_salary(request, employee_id):
    """Edit employee salary settings"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    if request.method == 'POST':
        monthly_salary = request.POST.get('monthly_salary')
        payment_day = request.POST.get('payment_day')
        payment_method = request.POST.get('payment_method')
        bank_name = request.POST.get('bank_name', '')
        bank_account_number = request.POST.get('bank_account_number', '')
        notes = request.POST.get('notes', '')
        
        try:
            # Update employee salary settings
            old_salary = employee.monthly_salary
            employee.monthly_salary = float(monthly_salary)
            employee.payment_day = int(payment_day)
            employee.payment_method = payment_method
            employee.bank_name = bank_name
            employee.bank_account_number = bank_account_number
            employee.save()
            
            # Create salary record for history
            SalaryRecord.objects.create(
                employee=employee,
                base_salary=float(monthly_salary),
                allowances=0,
                deductions=0,
                effective_date=timezone.now().date(),
                notes=notes or f'Salary updated from K{old_salary:,.2f} to K{monthly_salary}',
                created_by=request.user
            )
            
            # Log the action
            log_payroll_access(
                request.user,
                'edit_salary',
                f'Employee: {employee.user.get_full_name()}',
                request,
                f'Updated salary to K{monthly_salary}, payment day: {payment_day}'
            )
            
            messages.success(request, f'✓ Salary settings updated for {employee.user.get_full_name()}')
            return redirect('payroll:employee_list')
            
        except ValueError:
            messages.error(request, 'Invalid values entered')
    
    # Get salary history
    salary_records = SalaryRecord.objects.filter(employee=employee).select_related('created_by')[:10]
    
    # Generate list of days (1-31)
    days = list(range(1, 32))
    
    context = {
        'employee': employee,
        'salary_records': salary_records,
        'days': days,
    }
    
    return render(request, 'payroll/edit_salary.html', context)


@payroll_permission_required
def generate_period(request):
    """Generate a new payroll period"""
    from .models import PayrollPeriod, PayrollRecord
    from django.utils import timezone
    from datetime import date
    from calendar import monthrange
    
    if request.method == 'POST':
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        
        # Check if period already exists
        existing = PayrollPeriod.objects.filter(month=month, year=year).first()
        if existing:
            messages.warning(request, f'Payroll period for {existing} already exists')
            return redirect('payroll:period_detail', period_id=existing.id)
        
        # Create period
        period = PayrollPeriod.objects.create(
            month=month,
            year=year,
            status='open'
        )
        
        # Get all active employees with salary set
        employees = Employee.objects.filter(is_active=True, monthly_salary__gt=0)
        
        if not employees.exists():
            # Check if there are employees without salary
            employees_without_salary = Employee.objects.filter(is_active=True, monthly_salary=0).count()
            if employees_without_salary > 0:
                messages.error(
                    request, 
                    f'No employees with salary configured. Please set salaries for {employees_without_salary} employee(s) first.'
                )
            else:
                messages.error(request, 'No active employees found. Please sync employees first.')
            period.delete()
            return redirect('payroll:employee_list')
        
        # Generate records for each employee
        records_created = 0
        for employee in employees:
            # Calculate due date
            payment_day = min(employee.payment_day, monthrange(year, month)[1])
            due_date = date(year, month, payment_day)
            
            PayrollRecord.objects.create(
                period=period,
                employee=employee,
                expected_amount=employee.monthly_salary,
                due_date=due_date,
                status='pending'
            )
            records_created += 1
        
        # Update period totals
        period.update_totals()
        
        # Log the action
        log_payroll_access(
            request.user,
            'view_dashboard',
            f'Generated Payroll Period: {period}',
            request,
            f'Created {records_created} payment records'
        )
        
        messages.success(request, f'✓ Payroll period for {period} created with {records_created} employee records')
        return redirect('payroll:period_detail', period_id=period.id)
    
    # GET request - show form
    today = timezone.now().date()
    active_employees = Employee.objects.filter(is_active=True, monthly_salary__gt=0).count()
    employees_without_salary = Employee.objects.filter(is_active=True, monthly_salary=0).count()
    total_payroll = Employee.objects.filter(is_active=True).aggregate(
        total=Sum('monthly_salary')
    )['total'] or 0
    
    context = {
        'current_month': today.month,
        'current_year': today.year,
        'active_employees': active_employees,
        'employees_without_salary': employees_without_salary,
        'total_payroll': total_payroll,
    }
    
    return render(request, 'payroll/generate_period.html', context)
