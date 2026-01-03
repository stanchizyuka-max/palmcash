"""
Custom Django Admin Site for PalmCash.
Adds dashboard navigation and customizations.
"""
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.html import format_html


class PalmCashAdminSite(AdminSite):
    """
    Custom admin site with PalmCash branding and dashboard navigation.
    """
    site_header = "Palm Cash Administration"
    site_title = "Palm Cash Admin"
    index_title = "Welcome to Palm Cash Admin"
    
    def index(self, request, extra_context=None):
        """
        Override the admin index to add dashboard link.
        """
        extra_context = extra_context or {}
        
        # Add dashboard URL for the logged-in user
        if request.user.is_authenticated:
            extra_context['dashboard_url'] = reverse('dashboard:home')
            extra_context['user_role'] = request.user.get_role_display()
        
        return super().index(request, extra_context=extra_context)
    
    def each_context(self, request):
        """
        Add context variables to every admin page.
        """
        context = super().each_context(request)
        
        # Add dashboard URL to all admin pages
        if request.user.is_authenticated:
            context['dashboard_url'] = reverse('dashboard:home')
            context['user_role'] = request.user.get_role_display()
        
        return context


# Create the custom admin site instance
palm_cash_admin_site = PalmCashAdminSite(name='palmcash_admin')
