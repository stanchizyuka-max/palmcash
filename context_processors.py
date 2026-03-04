"""
Context processors for Palm Cash application
"""
from notifications.models import Notification


def notifications(request):
    """Add notification data to all templates"""
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
        }
    
    # Get unread notifications count
    unread_count = Notification.objects.filter(
        recipient=request.user,
        status__in=['pending', 'sent', 'delivered']
    ).count()
    
    # Get recent unread notifications (up to 5)
    recent_notifications = Notification.objects.filter(
        recipient=request.user,
        status__in=['pending', 'sent', 'delivered']
    ).order_by('-created_at')[:5]
    
    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_notifications,
    }
