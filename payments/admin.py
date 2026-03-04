from django.contrib import admin
from .models import PaymentSchedule, Payment, PaymentCollection, DefaultProvision, PassbookEntry

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

@admin.register(PaymentCollection)
class PaymentCollectionAdmin(admin.ModelAdmin):
    list_display = ['loan', 'collection_date', 'expected_amount', 'collected_amount', 'status', 'is_default']
    list_filter = ['status', 'collection_date', 'is_default', 'is_partial', 'is_late']
    search_fields = ['loan__application_number', 'loan__borrower__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'collection_date'
    
    actions = ['mark_as_completed', 'mark_as_default']
    
    def mark_as_completed(self, request, queryset):
        for collection in queryset:
            if collection.status != 'completed':
                collection.status = 'completed'
                collection.collected_by = request.user
                collection.save()
    mark_as_completed.short_description = "Mark selected collections as completed"
    
    def mark_as_default(self, request, queryset):
        queryset.update(is_default=True)
    mark_as_default.short_description = "Mark selected collections as default"
