from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from functools import wraps


def payroll_permission_required(view_func):
    """Decorator to check if user has payroll access"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        # Check if user has permission
        if not user.has_perm('payroll.can_view_payroll'):
            return render(request, 'dashboard/access_denied.html', {
                'message': 'You do not have permission to access payroll information. Please contact your administrator.'
            })
        
        return view_func(request, *args, **kwargs)
    return wrapper
