from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission
from django.shortcuts import render
from functools import wraps


def payroll_permission_required(view_func):
    """Decorator to check if user has explicit payroll access"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        # Check for explicit permission (not just superuser status)
        has_explicit_permission = False
        
        try:
            view_perm = Permission.objects.get(codename='can_view_payroll')
            
            # Check direct user permissions
            if user.user_permissions.filter(id=view_perm.id).exists():
                has_explicit_permission = True
            
            # Check group permissions
            if not has_explicit_permission:
                for group in user.groups.all():
                    if group.permissions.filter(id=view_perm.id).exists():
                        has_explicit_permission = True
                        break
        except Permission.DoesNotExist:
            pass
        
        if not has_explicit_permission:
            return render(request, 'dashboard/access_denied.html', {
                'message': 'You do not have permission to access payroll information. Please contact your administrator.'
            })
        
        return view_func(request, *args, **kwargs)
    return wrapper
