"""Custom JWT authentication that reads from httpOnly cookies."""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class JWTCookieAuthentication(JWTAuthentication):
    """JWT authentication that falls back to reading from httpOnly cookies.

    Tries Authorization header first (for API clients and tests),
    then falls back to the access_token cookie (for browser clients).
    """

    def authenticate(self, request):
        # Try header-based auth first (standard Bearer token)
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                try:
                    validated_token = self.get_validated_token(raw_token)
                    return self.get_user(validated_token), validated_token
                except (InvalidToken, TokenError):
                    pass

        # Fall back to cookie
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token.encode())
            return self.get_user(validated_token), validated_token
        except (InvalidToken, TokenError):
            return None
