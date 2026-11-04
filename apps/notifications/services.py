from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Notification, EmailLog


def create_notification(user, title, message, notification_type='info', link='', send_email=False):
    """Create in-app notification and optionally send email"""
    notif = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )
    if send_email and user.email:
        ok = send_notification_email(user, title, message)
        notif.email_sent = ok
        notif.save(update_fields=['email_sent'])
    return notif


def send_notification_email(user, subject, message):
    """Send a simple transactional email and log it"""
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ksgpvideo.com')
    try:
        send_mail(
            subject=f'[KSGP Video] {subject}',
            message=message,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=False,
        )
        EmailLog.objects.create(
            user=user,
            to_email=user.email,
            subject=subject,
            body_preview=message[:300],
            status='sent',
        )
        return True
    except Exception as e:
        EmailLog.objects.create(
            user=user,
            to_email=user.email,
            subject=subject,
            body_preview=message[:300],
            status='failed',
            error=str(e)[:500],
        )
        return False


def notify_campaign_status(campaign, status_label):
    create_notification(
        user=campaign.owner,
        title=f'Campaign {status_label}',
        message=f'Your campaign "{campaign.name}" is now {status_label}.',
        notification_type='campaign',
        link=f'/dashboard/campaigns/',
        send_email=True,
    )


def notify_payment_success(user, amount, credits):
    create_notification(
        user=user,
        title='Payment successful',
        message=f'Your payment of {amount} EUR was successful. {credits} credits have been added to your wallet.',
        notification_type='payment',
        link='/dashboard/wallet/',
        send_email=True,
    )
