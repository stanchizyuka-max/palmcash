from django.contrib import admin
from .models import Employee, SalaryRecord, PayrollPayment, PayrollAuditLog, PayrollPeriod, PayrollRecord


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_full_name', 'branch', 'position', 'monthly_salary', 'payment_day', 'hire_date', 'is_active']
    list_filter = ['is_active', 'branch', 'payment_method', 'hire_date']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'position', 'branch']
    raw_id_fields = ['user']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'employee_id', 'branch', 'position', 'hire_date', 'is_active')
        }),
        ('Salary Structure', {
            'fields': ('monthly_salary', 'payment_day', 'payment_method', 'bank_name', 'bank_account_number')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ['get_period', 'status', 'total_expected', 'total_paid', 'outstanding', 'payment_percentage', 'generated_date']
    list_filter = ['status', 'year', 'month']
    readonly_fields = ['total_expected', 'total_paid', 'generated_date', 'outstanding', 'payment_percentage']
    
    def get_period(self, obj):
        return str(obj)
    get_period.short_description = 'Period'
    
    def outstanding(self, obj):
        return f'K{obj.outstanding:,.2f}'
    outstanding.short_description = 'Outstanding'
    
    def payment_percentage(self, obj):
        return f'{obj.payment_percentage:.1f}%'
    payment_percentage.short_description = 'Paid %'


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'period', 'expected_amount', 'amount_paid', 'outstanding', 'due_date', 'payment_date', 'status']
    list_filter = ['status', 'period', 'due_date']
    search_fields = ['employee__employee_id', 'employee__user__first_name', 'employee__user__last_name']
    raw_id_fields = ['employee', 'processed_by']
    readonly_fields = ['outstanding']
    date_hierarchy = 'due_date'
    
    def outstanding(self, obj):
        return f'K{obj.outstanding:,.2f}'
    outstanding.short_description = 'Outstanding'


@admin.register(SalaryRecord)
class SalaryRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'base_salary', 'gross_salary', 'net_salary', 'effective_date']
    list_filter = ['effective_date']
    search_fields = ['employee__employee_id', 'employee__user__first_name', 'employee__user__last_name']
    raw_id_fields = ['employee', 'created_by']
    date_hierarchy = 'effective_date'


@admin.register(PayrollPayment)
class PayrollPaymentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payment_date', 'amount_paid', 'status', 'payment_method']
    list_filter = ['status', 'payment_date', 'payment_method']
    search_fields = ['employee__employee_id', 'reference_number']
    raw_id_fields = ['employee', 'salary_record', 'processed_by']
    date_hierarchy = 'payment_date'


@admin.register(PayrollAuditLog)
class PayrollAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'target', 'ip_address']
    readonly_fields = ['user', 'action', 'target', 'ip_address', 'timestamp', 'details']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
