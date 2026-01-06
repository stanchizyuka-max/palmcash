from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html


class CustomAdminSite(admin.AdminSite):
    """Custom admin site with back link to main system"""
    
    site_header = "Palm Cash Administration"
    site_title = "Palm Cash Admin"
    index_title = "Welcome to Palm Cash Administration"
    
    def index(self, request, extra_context=None):
        """Override index to add back link"""
        extra_context = extra_context or {}
        extra_context['dashboard_url'] = reverse('dashboard:dashboard')
        return super().index(request, extra_context)


# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')

