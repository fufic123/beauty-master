from typing import Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_email_notification(
    template_base: str, # шаблон эмейла без расширения
    context: dict,
    to_email: str,
    language: Optional[str] = None,
    event_type: Optional[str] = None,
) -> None:
    if event_type == "client_reminder":
        subject = render_to_string(f"subject/client_reminder_subject.txt", context).strip()
        html_body = render_to_string(f"email/client_reminder.html", context)
    else:
        subject = render_to_string(f"subject/{template_base}_subject.txt", context).strip()
        html_body = render_to_string(f"email/{template_base}.html", context)
  
    msg = EmailMultiAlternatives(
        subject=subject,
        body="Это письмо в HTML формате. Пожалуйста, включите HTML для корректного отображения.",
        from_email=getattr(settings, "EMAIL_HOST_USER", None),
        to=[to_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
    