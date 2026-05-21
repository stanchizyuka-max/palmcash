"""
Context processors for common functionality
"""

def unread_notifications(request):
    """
    Add unread notifications count to template context
    """
    if request.user.is_authenticated:
        from notifications.models import Notification
        count = Notification.objects.filter(
            recipient=request.user,
            status__in=['pending', 'sent', 'delivered']
        ).count()
        return {
            'unread_notifications_count': count,
        }
    return {
        'unread_notifications_count': 0,
    }


def acting_as_officer(request):
    """
    Add acting_as_officer to template context
    """
    return {
        'acting_as_officer': getattr(request, 'acting_as_officer', None),
    }
