"""Views for user authentication."""

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.tenants.models import UserTenantRole
from apps.users.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    VerifyEmailSerializer,
)
from apps.users.tasks import send_email_verification, send_invitation_email, send_password_reset


class RegisterView(APIView):
    """User registration endpoint.

    POST /api/auth/register/
    Creates a new user and sends email verification.
    Requires ALLOW_SELF_REGISTRATION to be True.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Register a new user.

        Request body:
            - email: User email address
            - password: User password (min 8 chars)

        Returns:
            - 201: User created successfully
            - 400: Validation error or registration disabled
        """
        if not getattr(settings, "ALLOW_SELF_REGISTRATION", True):
            return Response(
                {"detail": "Self-registration is disabled."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = user.generate_email_verification_token()
            send_email_verification.delay(user.id, token)
            return Response(
                {
                    "detail": "Registration successful. Please check your email.",
                    "email": user.email,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """Email verification endpoint.

    POST /api/auth/verify-email/
    Verifies user email using token from request body.
    Also supports GET with query param for email link compatibility.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """Verify email using token (email link compatibility).

        Query params:
            - token: Email verification token

        Returns:
            - 200: Email verified successfully
            - 400: Invalid or expired token
        """
        token = request.query_params.get("token")
        if not token:
            return Response(
                {"detail": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VerifyEmailSerializer(data={"token": token})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Email verified successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """Verify email using token in request body.

        Request body:
            - token: Email verification token

        Returns:
            - 200: Email verified successfully
            - 400: Invalid or expired token
        """
        token = request.data.get("token")
        if not token:
            return Response(
                {"detail": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VerifyEmailSerializer(data={"token": token})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Email verified successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    """Forgot password endpoint.

    POST /api/auth/forgot-password/
    Sends password reset email to user.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Request password reset email.

        Request body:
            - email: User email address

        Returns:
            - 200: Always returns success to prevent email enumeration
        """
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                user = User.objects.get(email__iexact=email)
                token = user.generate_password_reset_token()
                send_password_reset.delay(user.id, token)
            except User.DoesNotExist:
                pass
        return Response(
            {
                "detail": "If an account with that email exists, "
                "a password reset email has been sent."
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """Password reset endpoint.

    POST /api/auth/reset-password/
    Resets password using token from email.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Reset password using token.

        Request body:
            - token: Password reset token
            - new_password: New password (min 8 chars)
            - confirm_password: Confirm new password

        Returns:
            - 200: Password reset successfully
            - 400: Invalid token or validation error
        """
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            user.reset_password(serializer.validated_data["new_password"])
            return Response(
                {"detail": "Password reset successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Change password endpoint.

    POST /api/auth/change-password/
    Allows authenticated users to change their password.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change password for authenticated user.

        Request body:
            - current_password: Current password
            - new_password: New password (min 8 chars)
            - confirm_password: Confirm new password

        Returns:
            - 200: Password changed successfully
            - 400: Validation error
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data["new_password"])
            request.user.save()
            return Response(
                {"detail": "Password changed successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """User profile endpoint.

    PATCH /api/users/me/
    Get and update current user profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """Update current user profile."""
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login endpoint with tenant list.

    POST /api/auth/login/
    Returns access_token, refresh_token, and tenant_list in body.
    Also sets JWT tokens as httpOnly cookies for convenience.
    """

    def post(self, request, *args, **kwargs):
        """Obtain JWT token pair with tenant information.

        Request body:
            - email: User email
            - password: User password

        Returns:
            - 200: access_token, refresh_token, tenant_list in body
                   + httpOnly cookies for both tokens
            - 401: Invalid credentials
        """
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = response.user if hasattr(response, "user") else None
            if user is None:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                email = request.data.get("email", "").lower()
                user = User.objects.filter(email__iexact=email).first()

            if user:
                notifications, count = user.get_unread_notifications()
                response.data["tenant_list"] = user.get_tenant_list()
                response.data["unread_notifications"] = notifications
                response.data["unread_notifications_count"] = count

                access_token = response.data.get("access")
                refresh_token = response.data.get("refresh")

                if access_token:
                    response.set_cookie(
                        key="access_token",
                        value=access_token,
                        httponly=True,
                        secure=getattr(settings, "COOKIE_SECURE", False),
                        samesite="Lax",
                        max_age=3600,
                    )
                if refresh_token:
                    response.set_cookie(
                        key="refresh_token",
                        value=refresh_token,
                        httponly=True,
                        secure=getattr(settings, "COOKIE_SECURE", False),
                        samesite="Lax",
                        max_age=604800,
                    )

        return response


class CustomTokenRefreshView(TokenRefreshView):
    """Refresh access token using httpOnly cookie.

    POST /api/auth/refresh/
    Reads refresh_token from cookie, returns new access_token as cookie.
    """

    def post(self, request, *args, **kwargs):
        """Refresh access token.

        Returns:
            - 200: New access_token as httpOnly cookie
            - 401: Invalid or expired refresh token
        """
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            token = RefreshToken(refresh_token)
            access = str(token.access_token)
            response = Response(
                {"detail": "Token refreshed successfully."},
                status=status.HTTP_200_OK,
            )
            response.set_cookie(
                key="access_token",
                value=access,
                httponly=True,
                secure=getattr(settings, "COOKIE_SECURE", False),
                samesite="Lax",
                max_age=3600,
            )
            return response
        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    """Logout endpoint that clears JWT cookies.

    POST /api/auth/logout/
    Clears access_token and refresh_token cookies.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Clear authentication cookies.

        Returns:
            - 200: Logged out successfully
        """
        response = Response(
            {"detail": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class SelectTenantView(APIView):
    """Select active tenant endpoint.

    POST /api/auth/select-tenant/
    Sets the active tenant context for the current session.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Select active tenant for the current user.

        Request body:
            - tenant_id: UUID of tenant to select

        Returns:
            - 200: Tenant selected successfully
            - 400: Invalid tenant or no access
        """
        tenant_id = request.data.get("tenant_id")
        if not tenant_id:
            return Response(
                {"detail": "tenant_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        has_access = UserTenantRole.objects.filter(
            user=request.user,
            tenant_id=tenant_id,
            tenant__is_active=True,
        ).exists()

        if not has_access:
            return Response(
                {"detail": "You do not have access to this tenant."},
                status=status.HTTP_403_FORBIDDEN,
            )

        from core.middleware import set_current_tenant
        from apps.tenants.models import Tenant

        try:
            tenant = Tenant.objects.get(id=tenant_id)
            set_current_tenant(tenant)
            return Response(
                {
                    "detail": "Tenant selected successfully.",
                    "tenant_id": str(tenant.id),
                }
            )
        except Tenant.DoesNotExist:
            return Response(
                {"detail": "Tenant not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class InvitationCreateView(APIView):
    """Create and send an invitation email.

    POST /api/users/invitations/
    Admin or Owner only. Creates Invitation and fires Celery email task.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"detail": "email is required."}, status=status.HTTP_400_BAD_REQUEST)

        from apps.users.models import CustomUser, Invitation
        from django.utils import timezone

        if CustomUser.objects.filter(email=email).exists():
            return Response(
                {"detail": "El usuario ya existe. Puedes agregarlo directamente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pending = Invitation.objects.filter(
            email=email, accepted_at__isnull=True, expires_at__gt=timezone.now()
        ).exists()
        if pending:
            return Response(
                {"detail": "Ya existe una invitación pendiente para este email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation = Invitation.objects.create(email=email, invited_by=request.user)
        send_invitation_email.delay(str(invitation.id))

        return Response(
            {"detail": f"Invitación enviada a {email}.", "invitation_id": str(invitation.id)},
            status=status.HTTP_201_CREATED,
        )


class InvitationAcceptView(APIView):
    """Validate token (GET) or accept invitation and create account (POST).

    GET  /api/users/invitations/{token}/  — returns email for pre-fill
    POST /api/users/invitations/{token}/  — creates user + joins tenant
    """

    permission_classes = [AllowAny]

    def get(self, request, token):
        from apps.users.models import Invitation

        try:
            invitation = Invitation.objects.get(token=token)
        except Invitation.DoesNotExist:
            return Response({"detail": "Invitación no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if not invitation.is_valid:
            return Response({"detail": "La invitación ha expirado o ya fue usada."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"email": invitation.email, "expires_at": invitation.expires_at})

    def post(self, request, token):
        from apps.users.models import Invitation, CustomUser
        from apps.tenants.models import Tenant, UserTenantRole

        try:
            invitation = Invitation.objects.get(token=token)
        except Invitation.DoesNotExist:
            return Response({"detail": "Invitación no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if not invitation.is_valid:
            return Response({"detail": "La invitación ha expirado o ya fue usada."}, status=status.HTTP_400_BAD_REQUEST)

        password = request.data.get("password", "").strip()
        if not password or len(password) < 8:
            return Response({"detail": "La contraseña debe tener al menos 8 caracteres."}, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(email=invitation.email).exists():
            return Response({"detail": "Ya existe una cuenta con este email."}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.create_user(
            email=invitation.email,
            password=password,
            is_email_verified=True,
        )

        main_slug = getattr(settings, "MAIN_TENANT_SLUG", "ximbra")
        try:
            tenant = Tenant.objects.get(slug=main_slug, is_active=True)
            UserTenantRole.objects.get_or_create(
                user=user, tenant=tenant, defaults={"role": UserTenantRole.Role.MEMBER}
            )
        except Tenant.DoesNotExist:
            pass

        invitation.accept()

        return Response(
            {"detail": "Cuenta creada exitosamente. Puedes iniciar sesión."},
            status=status.HTTP_201_CREATED,
        )
