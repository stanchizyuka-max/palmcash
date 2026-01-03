from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Permission, User as DjangoUser
from django.contrib.contenttypes.models import ContentType
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_verified', 'date_joined']
    list_filter = ['role', 'is_verified', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'national_id']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('LoanVista Profile', {
            'fields': ('role', 'phone_number', 'address', 'date_of_birth', 'national_id', 'profile_picture', 'is_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('LoanVista Profile', {
            'fields': ('role', 'phone_number', 'email', 'first_name', 'last_name')
        }),
    )

# Register Permission and ContentType models
admin.site.register(Permission)
admin.site.register(ContentType)

# Register Django's built-in User model for compatibility with existing links
class DjangoUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['date_joined', 'last_login']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

# Try to register Django's User model
try:
    admin.site.register(DjangoUser, DjangoUserAdmin)
except admin.sites.AlreadyRegistered:
    # If already registered, unregister and re-register with our admin
    admin.site.unregister(DjangoUser)
    admin.site.register(DjangoUser, DjangoUserAdmin)