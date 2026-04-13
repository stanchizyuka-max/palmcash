from django.contrib import admin
from .models import Employee, SalaryRecord, PayrollPayment, PayrollAuditLog


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_full_name', 'department', 'position', 'hire_date', 'is_active']
    list_filter = ['is_active', 'department', 'hire_date']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'position']
    raw_id_fields = ['user']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'


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
