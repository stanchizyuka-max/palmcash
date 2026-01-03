"""
Context processors for making data available to all templates
"""

def unread_notifications(request):
    """
    Add unread notification count to all template contexts
    """
    if request.user.is_authenticated:
        try:
            from notifications.models import Notification
            unread_count = Notification.objects.filter(
                recipient=request.user,
                status__in=['pending', 'sent', 'delivered']
            ).count()
            return {'unread_notifications_count': unread_count}
        except:
            return {'unread_notifications_count': 0}
    return {'unread_notifications_count': 0}
