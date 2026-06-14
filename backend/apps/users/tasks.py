"""Celery tasks for async email sending."""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from config.celery import app


@app.task
def send_email_verification(user_id: int, token: str):
    """Send email verification link asynchronously."""
    from apps.users.models import CustomUser

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    verify_url = f"{frontend_url}/verify-email/?token={token}"

    context = {
        "user_email": user.email,
        "verify_url": verify_url,
        "frontend_url": frontend_url,
    }

    subject = "Verify your email address"
    text_body = render_to_string("emails/verify_email.txt", context)
    html_body = render_to_string("emails/verify_email.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


@app.task
def send_password_reset(user_id: int, token: str):
    """Send password reset link asynchronously."""
    from apps.users.models import CustomUser

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    reset_url = f"{frontend_url}/reset-password/?token={token}"

    context = {
        "user_email": user.email,
        "reset_url": reset_url,
        "frontend_url": frontend_url,
    }

    subject = "Reset your password"
    text_body = render_to_string("emails/password_reset.txt", context)
    html_body = render_to_string("emails/password_reset.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


@app.task
def send_invitation_email(invitation_id: str):
    """Send invitation email with accept link."""
    from apps.users.models import Invitation

    try:
        invitation = Invitation.objects.select_related("invited_by").get(id=invitation_id)
    except Invitation.DoesNotExist:
        return

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    accept_url = f"{frontend_url}/invitations/{invitation.token}/accept/"

    context = {
        "invited_by_email": invitation.invited_by.email if invitation.invited_by else "el equipo",
        "accept_url": accept_url,
        "frontend_url": frontend_url,
        "expires_at": invitation.expires_at.strftime("%d/%m/%Y %H:%M"),
    }

    subject = "Te han invitado a Ximbra"
    text_body = render_to_string("emails/invitation.txt", context)
    html_body = render_to_string("emails/invitation.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invitation.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
