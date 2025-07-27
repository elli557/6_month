from celery import shared_task
import time
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_otp_email(user_email, code):
    subject = "Ваш код подтверждения"
    message = f"Ваш код подтверждения: {code}"
    from_email = settings.EMAIL_HOST_USER

    send_mail(
        subject,
        message,
        from_email,
        [user_email],
        fail_silently=False,
    )

@shared_task
def send_daily_report():
    print("sending daily report ....")
    time.sleep(50)
    print("daily report sent")
