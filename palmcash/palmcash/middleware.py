"""
Custom middleware for Palm Cash application
"""
from django.middleware.csrf import get_token


class EnsureCsrfCookieMiddleware:
    """
    Middleware to ensure CSRF token is always set in cookies.
    This fixes CSRF validation issues on POST requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Ensure CSRF token is set for all GET requests
        if request.method == 'GET':
            get_token(request)
        
        response = self.get_response(request)
        return response
