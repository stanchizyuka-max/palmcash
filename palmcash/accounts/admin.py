from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Permission, User as DjangoUser
from django.contrib.contenttypes.models import ContentType
from .models import User


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


class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'codename']
    list_filter = ['content_type']
    search_fields = ['name', 'codename']


class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ['app_label', 'model']
    list_filter = ['app_label']
    search_fields = ['app_label', 'model']


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


# Register models with custom admin site
def register_admin_models():
    """Register all models with the custom admin site"""
    from common.admin import custom_admin_site
    custom_admin_site.register(User, UserAdmin)
    custom_admin_site.register(Permission, PermissionAdmin)
    custom_admin_site.register(ContentType, ContentTypeAdmin)
    custom_admin_site.register(DjangoUser, DjangoUserAdmin)


# Call registration function
register_admin_models()