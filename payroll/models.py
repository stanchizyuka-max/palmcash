from django.db import models
from django.utils import timezone
from accounts.models import User


class Employee(models.Model):
    """Employee record linked to User account"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    branch = models.CharField(max_length=100, blank=True, help_text='Branch where employee works')
    position = models.CharField(max_length=100)
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Salary Structure
    monthly_salary = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text='Base monthly salary amount'
    )
    payment_day = models.IntegerField(
        default=30,
        help_text='Day of month for salary payment (1-31, use 31 for last day)'
    )
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('bank_transfer', 'Bank Transfer'),
            ('cash', 'Cash'),
            ('mobile_money', 'Mobile Money'),
        ],
        default='bank_transfer'
    )
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        permissions = [
            ('can_view_payroll', 'Can view payroll information'),
            ('can_manage_payroll', 'Can manage payroll records'),
            ('can_generate_payroll_reports', 'Can generate payroll reports'),
        ]
        ordering = ['employee_id']
    
    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"
    
    @property
    def department(self):
        """Backward compatibility - return branch as department"""
        return self.branch or 'Unassigned'


class PayrollPeriod(models.Model):
    """Monthly payroll period"""
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('processing', 'Processing'),
        ('closed', 'Closed'),
    ]
    
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    total_expected = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    generated_date = models.DateTimeField(auto_now_add=True)
    closed_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['month', 'year']
    
    def __str__(self):
        return f"{self.get_month_display()} {self.year}"
    
    @property
    def outstanding(self):
        return self.total_expected - self.total_paid
    
    @property
    def payment_percentage(self):
        if self.total_expected > 0:
            return (self.total_paid / self.total_expected) * 100
        return 0
    
    def update_totals(self):
        """Recalculate totals from payroll records"""
        from django.db.models import Sum
        records = self.payroll_records.all()
        self.total_expected = records.aggregate(Sum('expected_amount'))['expected_amount__sum'] or 0
        self.total_paid = records.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        self.save()


class PayrollRecord(models.Model):
    """Individual employee payroll record for a period"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('overdue', 'Overdue'),
    ]
    
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payroll_records')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payroll_records')
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payroll_records')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date', 'employee__employee_id']
        unique_together = ['period', 'employee']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.period}"
    
    @property
    def outstanding(self):
        return self.expected_amount - self.amount_paid
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status == 'paid':
            return False
        return self.due_date < timezone.now().date()
    
    def update_status(self):
        """Auto-update status based on payment"""
        from django.utils import timezone
        
        if self.amount_paid >= self.expected_amount:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        elif self.due_date < timezone.now().date():
            self.status = 'overdue'
        else:
            self.status = 'pending'
        
        self.save()


class SalaryRecord(models.Model):
    """Salary information for employees"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_records')
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Housing, transport, etc.')
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Tax, insurance, etc.')
    effective_date = models.DateField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_salaries')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-effective_date']
    
    @property
    def gross_salary(self):
        return self.base_salary + self.allowances
    
    @property
    def net_salary(self):
        return self.base_salary + self.allowances - self.deductions
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.effective_date}"


class PayrollPayment(models.Model):
    """Record of salary payments"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payments')
    salary_record = models.ForeignKey(SalaryRecord, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='Bank Transfer')
    reference_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='processed_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.payment_date} - {self.get_status_display()}"


class PayrollAuditLog(models.Model):
    """Audit trail for payroll access"""
    ACTION_CHOICES = [
        ('view_dashboard', 'Viewed Dashboard'),
        ('view_employee', 'Viewed Employee'),
        ('view_salary', 'Viewed Salary'),
        ('edit_salary', 'Edited Salary'),
        ('create_payment', 'Created Payment'),
        ('export_report', 'Exported Report'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payroll_audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp}"
