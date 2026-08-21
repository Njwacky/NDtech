"""
Authentication classes for the REST API.

Django REST Framework's SessionAuthentication returns HTTP 403 when a request
is not authenticated, which makes it impossible for API clients to distinguish
"you need to log in" from "you are logged in but not allowed". These classes
return HTTP 401 with a DRF `WWW-Authenticate` header so the response follows
standard HTTP semantics.
"""
from rest_framework import authentication, exceptions


class SessionAuthentication401(authentication.SessionAuthentication):
    """Session authentication that returns 401 instead of 403 when unauthenticated."""

    def authenticate_header(self, request):
        return 'Session'

    def handle_authentication_failure(self, request=None):
        raise exceptions.NotAuthenticated(
            'Authentication credentials were not provided.'
        )


class BasicAuthentication401(authentication.BasicAuthentication):
    """Basic authentication that returns 401 instead of 403 when unauthenticated."""

    def authenticate_header(self, request):
        return 'Basic realm="api"'

    def handle_authentication_failure(self, request=None):
        raise exceptions.NotAuthenticated(
            'Authentication credentials were not provided.'
        )
