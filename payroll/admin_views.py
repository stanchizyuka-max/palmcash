from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.sessions.models import Session
from django.utils import timezone
from accounts.models import User


def clear_user_sessions(user):
    """Clear all active sessions for a user to force re-authentication"""
    # Get all active sessions
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    
    for session in active_sessions:
        session_data = session.get_decoded()
        if session_data.get('_auth_user_id') == str(user.id):
            session.delete()


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
        report_perm = Permission.objects.get(codename='can_generate_payroll_reports')
        
        if action == 'grant':
            user.user_permissions.add(view_perm, manage_perm, report_perm)
            messages.success(request, f'✓ Granted payroll access to {user.get_full_name()}. User must logout and login again for changes to take effect.')
        elif action == 'revoke':
            # Remove all payroll permissions
            user.user_permissions.remove(view_perm, manage_perm, report_perm)
            
            # Also remove from any groups that might have payroll permissions
            for group in user.groups.all():
                if group.permissions.filter(codename__in=['can_view_payroll', 'can_manage_payroll', 'can_generate_payroll_reports']).exists():
                    user.groups.remove(group)
            
            # Clear user's sessions to force re-login (this applies changes immediately)
            clear_user_sessions(user)
            
            messages.warning(request, f'✗ Revoked payroll access from {user.get_full_name()}. User has been logged out and must login again.')
        
        return redirect('payroll:manage_access')
    
    return render(request, 'payroll/manage_access.html', {
        'users_with_access': users_with_access,
        'users_without_access': users_without_access,
    })
