from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
import time


class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        if not getattr(request, 'is_secure', lambda: False)():
            # Only set HSTS on HTTPS in production via settings
            pass
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Simple in-memory rate limit for sensitive endpoints (production should use Redis)"""
    def process_request(self, request):
        # Placeholder – real implementation uses django-ratelimit or Redis
        return None
