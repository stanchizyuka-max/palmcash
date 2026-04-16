"""
Views for user activity monitoring and audit logs
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, timedelta
from .models import UserLoginSession, UserActivityLog

User = get_user_model()


@login_required
def user_audit_list(request):
    """Display list of users with activity overview"""
    
    # Only admins and managers can view audit logs
    if request.user.role not in ['admin', 'manager']:
        return render(request, 'dashboard/access_denied.html')
    
    # Get all users except borrowers (or include based on preference)
    users = User.objects.filter(
        role__in=['admin', 'manager', 'loan_officer']
    ).select_related().order_by('-last_login')
    
    # Apply filters
    role_filter = request.GET.get('role', '')
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Get currently active users from Django sessions for filtering
    from django.contrib.sessions.models import Session
    from django.utils import timezone as tz
    
    active_sessions = Session.objects.filter(expire_date__gte=tz.now())
    active_user_ids_for_filter = set()
    
    for session in active_sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id:
            active_user_ids_for_filter.add(int(user_id))
    
    if status_filter == 'active':
        # Users with active Django sessions
        users = users.filter(id__in=active_user_ids_for_filter)
    elif status_filter == 'offline':
        # Users without active Django sessions
        users = users.exclude(id__in=active_user_ids_for_filter)
    
    # Get currently active users from Django sessions
    from django.contrib.sessions.models import Session
    from django.utils import timezone as tz
    
    active_sessions = Session.objects.filter(expire_date__gte=tz.now())
    active_user_ids = set()
    
    for session in active_sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id:
            active_user_ids.add(int(user_id))
    
    # Enrich users with activity data
    user_data = []
    today = date.today()
    
    for user in users:
        # Try to get last session, fallback to Django's last_login
        last_session = user.login_sessions.first() if hasattr(user, 'login_sessions') else None
        last_login = None
        
        if last_session:
            last_login = last_session.login_time
        elif user.last_login:
            # Fallback to Django's built-in last_login
            last_login = user.last_login
        
        # Get actions today
        actions_today = 0
        if hasattr(user, 'activity_logs'):
            actions_today = user.activity_logs.filter(timestamp__date=today).count()
        
        # Check if currently active - use Django sessions as primary source
        is_active = user.id in active_user_ids
        
        # If not found in Django sessions, check our tracking
        if not is_active and last_session and last_session.is_active:
            time_since_login = timezone.now() - last_session.login_time
            is_active = time_since_login < timedelta(minutes=30)
        
        user_data.append({
            'user': user,
            'last_login': last_login,
            'actions_today': actions_today,
            'is_active': is_active,
        })
    
    context = {
        'user_data': user_data,
        'role_filter': role_filter,
        'search': search,
        'status_filter': status_filter,
    }
    
    return render(request, 'accounts/user_audit_list.html', context)


@login_required
def user_activity_detail(request, user_id):
    """Display detailed activity dashboard for a specific user"""
    
    # Only admins and managers can view audit logs
    if request.user.role not in ['admin', 'manager']:
        return render(request, 'dashboard/access_denied.html')
    
    target_user = get_object_or_404(User, id=user_id)
    
    # Get last login session with fallback
    last_session = None
    active_session = None
    if hasattr(target_user, 'login_sessions'):
        last_session = target_user.login_sessions.first()
        active_session = target_user.login_sessions.filter(is_active=True).first()
    
    # Get last activity with fallback
    last_activity = None
    if hasattr(target_user, 'activity_logs'):
        last_activity = target_user.activity_logs.first()
    
    # Check if currently active - use Django sessions as primary source
    from django.contrib.sessions.models import Session
    from django.utils import timezone as tz
    
    is_active = False
    active_sessions = Session.objects.filter(expire_date__gte=tz.now())
    
    for session in active_sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id and int(user_id) == target_user.id:
            is_active = True
            break
    
    # If not found in Django sessions, check our tracking
    if not is_active and active_session:
        time_since_login = timezone.now() - active_session.login_time
        is_active = time_since_login < timedelta(minutes=30)
    
    # Activity statistics
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    actions_today = 0
    actions_this_week = 0
    critical_actions = 0
    logs = []
    
    if hasattr(target_user, 'activity_logs'):
        actions_today = target_user.activity_logs.filter(timestamp__date=today).count()
        actions_this_week = target_user.activity_logs.filter(timestamp__date__gte=week_ago).count()
        critical_actions = target_user.activity_logs.filter(severity='critical').count()
        
        # Get activity logs with filters
        logs = target_user.activity_logs.all()
        
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        action_filter = request.GET.get('action', '')
        severity_filter = request.GET.get('severity', '')
        
        if date_from:
            logs = logs.filter(timestamp__date__gte=date_from)
        if date_to:
            logs = logs.filter(timestamp__date__lte=date_to)
        if action_filter:
            logs = logs.filter(action=action_filter)
        if severity_filter:
            logs = logs.filter(severity=severity_filter)
    else:
        # No activity logs table yet
        date_from = ''
        date_to = ''
        action_filter = ''
        severity_filter = ''
    # Paginate logs
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50) if logs else Paginator([], 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get recent login sessions
    recent_sessions = []
    if hasattr(target_user, 'login_sessions'):
        recent_sessions = target_user.login_sessions.all()[:10]
    
    # Activity timeline (last 20 actions)
    timeline_actions = []
    if hasattr(target_user, 'activity_logs'):
        timeline_actions = target_user.activity_logs.all()[:20]
    
    # Action breakdown
    action_breakdown = []
    if hasattr(target_user, 'activity_logs'):
        action_breakdown = target_user.activity_logs.values('action').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
    
    # Get additional audit logs
    from clients.models import ApprovalAuditLog, DisbursementAuditLog, CollectionAuditLog
    
    approval_logs = ApprovalAuditLog.objects.filter(
        performed_by=target_user
    ).select_related('loan', 'loan__borrower').order_by('-timestamp')[:20]
    
    disbursement_logs = DisbursementAuditLog.objects.filter(
        performed_by=target_user
    ).select_related('loan', 'loan__borrower').order_by('-timestamp')[:20]
    
    collection_logs = CollectionAuditLog.objects.filter(
        performed_by=target_user
    ).select_related('loan', 'loan__borrower').order_by('-timestamp')[:20]
    
    # Count totals
    total_approvals = ApprovalAuditLog.objects.filter(
        performed_by=target_user
    ).count()
    
    total_disbursements = DisbursementAuditLog.objects.filter(
        performed_by=target_user
    ).count()
    
    total_collections = CollectionAuditLog.objects.filter(
        performed_by=target_user
    ).count()
    
    context = {
        'target_user': target_user,
        'last_session': last_session,
        'active_session': active_session,
        'last_activity': last_activity,
        'is_active': is_active,
        'actions_today': actions_today,
        'actions_this_week': actions_this_week,
        'critical_actions': critical_actions,
        'page_obj': page_obj,
        'recent_sessions': recent_sessions,
        'timeline_actions': timeline_actions,
        'action_breakdown': action_breakdown,
        'approval_logs': approval_logs,
        'disbursement_logs': disbursement_logs,
        'collection_logs': collection_logs,
        'total_approvals': total_approvals,
        'total_disbursements': total_disbursements,
        'total_collections': total_collections,
        'date_from': date_from,
        'date_to': date_to,
        'action_filter': action_filter,
        'severity_filter': severity_filter,
        'action_choices': UserActivityLog.ACTION_CHOICES,
        'severity_choices': UserActivityLog.SEVERITY_CHOICES,
    }
    
    return render(request, 'accounts/user_activity_detail.html', context)


def log_user_activity(user, action, description, target_type='', target_id='', 
                      target_name='', severity='info', old_value='', new_value='', 
                      request=None):
    """
    Helper function to log user activity
    
    Usage:
        from accounts.audit_views import log_user_activity
        log_user_activity(
            user=request.user,
            action='loan_approve',
            description=f'Approved loan {loan.application_number}',
            target_type='loan',
            target_id=str(loan.id),
            target_name=loan.application_number,
            severity='critical',
            request=request
        )
    """
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    UserActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        severity=severity,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address
    )


def log_login(user, request):
    """Log user login"""
    ip_address = None
    user_agent = ''
    session_key = ''
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        session_key = request.session.session_key or ''
    
    # Create login session
    UserLoginSession.objects.create(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        session_key=session_key,
        is_active=True
    )
    
    # Log activity
    log_user_activity(
        user=user,
        action='login',
        description=f'User logged in from {ip_address}',
        severity='info',
        request=request
    )


def log_logout(user, request):
    """Log user logout"""
    # Mark active sessions as inactive
    active_sessions = user.login_sessions.filter(is_active=True)
    for session in active_sessions:
        session.is_active = False
        session.logout_time = timezone.now()
        session.save()
    
    # Log activity
    log_user_activity(
        user=user,
        action='logout',
        description='User logged out',
        severity='info',
        request=request
    )
