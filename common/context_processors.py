"""
Context processors for common functionality
"""

def acting_as_officer(request):
    """
    Add acting_as_officer to template context
    """
    return {
        'acting_as_officer': getattr(request, 'acting_as_officer', None),
    }
