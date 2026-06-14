"""Users URL Configuration."""

from django.urls import path

from apps.users.views import (
    ChangePasswordView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    ForgotPasswordView,
    InvitationAcceptView,
    InvitationCreateView,
    InvitationListView,
    LogoutView,
    ProfileView,
    RegisterView,
    ResetPasswordView,
    SelectTenantView,
    UserListView,
    UserToggleView,
    VerifyEmailView,
)

urlpatterns = [
    # Auth
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
    # Invitaciones
    path("invitations/", InvitationCreateView.as_view(), name="invitation_create"),
    path("invitations/list/", InvitationListView.as_view(), name="invitation_list"),
    path("invitations/<uuid:token>/", InvitationAcceptView.as_view(), name="invitation_accept"),
    # Gestión de usuarios (superuser)
    path("list/", UserListView.as_view(), name="user_list"),
    path("<int:pk>/toggle/", UserToggleView.as_view(), name="user_toggle"),
]
