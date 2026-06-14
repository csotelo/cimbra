"""Users URL Configuration."""

from django.urls import path

from apps.users.views import (
    ChangePasswordView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    ForgotPasswordView,
    InvitationAcceptView,
    InvitationCreateView,
    LogoutView,
    ProfileView,
    RegisterView,
    ResetPasswordView,
    SelectTenantView,
    VerifyEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset_password"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("select-tenant/", SelectTenantView.as_view(), name="select_tenant"),
    path("me/", ProfileView.as_view(), name="profile"),
    path("invitations/", InvitationCreateView.as_view(), name="invitation_create"),
    path("invitations/<uuid:token>/", InvitationAcceptView.as_view(), name="invitation_accept"),
]
