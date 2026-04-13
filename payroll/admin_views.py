from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import Permission
from accounts.models import User


@staff_member_required
def manage_payroll_access(request):
    """Admin view to manage payroll access for users"""
    
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can manage payroll access')
        return redirect('admin:index')
    
    # Get all admin and manager users
    eligible_users = User.objects.filter(
        role__in=['admin', 'manager'],
        is_active=True
    ).order_by('first_name', 'last_name')
    
    # Check who has payroll access
    users_with_access = []
    users_without_access = []
    
    for user in eligible_users:
        if user.has_perm('payroll.can_view_payroll'):
            users_with_access.append(user)
        else:
            users_without_access.append(user)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        user = get_object_or_404(User, id=user_id)
        view_perm = Permission.objects.get(codename='can_view_payroll')
        manage_perm = Permission.objects.get(codename='can_manage_payroll')
        
        if action == 'grant':
            user.user_permissions.add(view_perm, manage_perm)
            messages.success(request, f'✓ Granted payroll access to {user.get_full_name()}')
        elif action == 'revoke':
            user.user_permissions.remove(view_perm, manage_perm)
            messages.warning(request, f'✗ Revoked payroll access from {user.get_full_name()}')
        
        return redirect('payroll:manage_access')
    
    return render(request, 'payroll/manage_access.html', {
        'users_with_access': users_with_access,
        'users_without_access': users_without_access,
    })
