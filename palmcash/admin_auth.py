"""
Admin authentication middleware and utilities for PalmCash.
Prevents managers from accessing the Django admin dashboard without proper credentials.
"""
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect


class AdminAccessMiddleware:
    """
    Middleware to restrict manager access to Django admin dashboard.
    Managers must provide admin credentials to access /admin/
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_paths = ['/admin/', '/admin']
    
    def __call__(self, request):
        # Check if accessing admin paths
        if any(request.path.startswith(path) for path in self.admin_paths):
            # Allow superusers and admins
            if request.user.is_authenticated:
                if request.user.is_superuser or request.user.role == 'admin':
                    return self.get_response(request)
                
                # Managers are not allowed
                if request.user.role == 'manager':
                    return redirect('admin_auth:manager_login')
        
        return self.get_response(request)


@require_http_methods(["GET", "POST"])
@csrf_protect
def manager_admin_login(request):
    """
    View for managers to enter admin credentials before accessing admin dashboard.
    Managers must authenticate as an admin user to proceed.
    """
    error = None
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        # Authenticate the provided credentials
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if the authenticated user is an admin
            if user.is_superuser or user.role == 'admin':
                # Store admin credentials in session for this manager
                request.session['admin_verified'] = True
                request.session['admin_username'] = username
                
                # Redirect to admin dashboard
                return redirect('admin:index')
            else:
                error = 'Provided credentials are not for an admin account. Only admin credentials are accepted.'
        else:
            error = 'Invalid username or password. Please try again.'
    
    # Get manager name if authenticated, otherwise use default
    manager_name = 'Manager'
    if request.user.is_authenticated:
        manager_name = request.user.get_full_name() or request.user.username
    
    context = {
        'error': error,
        'manager_name': manager_name,
        'dashboard_url': reverse('dashboard:dashboard'),
    }
    
    return render(request, 'admin_auth/manager_login.html', context)


@login_required
def admin_access_denied(request):
    """
    View shown when a non-admin user tries to access admin without proper credentials.
    """
    return render(request, 'admin_auth/access_denied.html', {
        'user_role': request.user.get_role_display(),
        'dashboard_url': reverse('dashboard:dashboard'),
    })
