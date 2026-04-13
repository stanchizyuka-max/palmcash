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
