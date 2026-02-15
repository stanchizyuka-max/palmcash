"""
Common views for Palm Cash application
"""
from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def csrf_failure(request, reason=""):
    """
    Custom CSRF failure view with debugging information
    """
    context = {
        'reason': reason,
        'referer': request.META.get('HTTP_REFERER', 'Unknown'),
        'origin': request.META.get('HTTP_ORIGIN', 'Unknown'),
        'host': request.META.get('HTTP_HOST', 'Unknown'),
    }
    return render(request, 'common/csrf_error.html', context, status=403)
