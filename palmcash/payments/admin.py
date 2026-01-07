from django.contrib import admin
from .models import PaymentSchedule, Payment

@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    list_display = ['loan', 'installment_number', 'due_date', 'total_amount', 'is_paid']
    list_filter = ['is_paid', 'due_date']
    search_fields = ['loan__application_number', 'loan__borrower__username']
    readonly_fields = ['loan', 'installment_number']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'loan', 'amount', 'payment_date', 'status']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['payment_number', 'loan__application_number', 'reference_number']
    readonly_fields = ['payment_number']
