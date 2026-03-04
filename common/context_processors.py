"""
Context processors for making data available to all templates
"""

def unread_notifications(request):
    """
    Add unread notification count and recent notifications to all template contexts
    """
    if request.user.is_authenticated:
        try:
            from notifications.models import Notification
            unread_count = Notification.objects.filter(
                recipient=request.user,
                status__in=['pending', 'sent', 'delivered']
            ).count()
            
            recent_notifications = Notification.objects.filter(
                recipient=request.user,
                status__in=['pending', 'sent', 'delivered']
            ).order_by('-created_at')[:5]
            
            return {
                'unread_notifications_count': unread_count,
                'recent_notifications': recent_notifications,
            }
        except:
            return {
                'unread_notifications_count': 0,
                'recent_notifications': [],
            }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }

