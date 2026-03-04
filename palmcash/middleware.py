from django.middleware.csrf import CsrfViewMiddleware


class EnsureCsrfCookieMiddleware(CsrfViewMiddleware):
    """
    Middleware that ensures CSRF cookie is set on all responses.
    This helps prevent CSRF 403 errors on login and other forms.
    """
    def process_response(self, request, response):
        # Ensure CSRF cookie is set
        if not request.META.get('CSRF_COOKIE'):
            self.process_request(request)
        return super().process_response(request, response)
