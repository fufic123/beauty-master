def send_email_notification(email: str, subject: str, message: str):
    """
    Simulate sending an email notification.
    In a real-world scenario, this would integrate with an email service provider.
    """
    print(f"Sending email to {email} with subject '{subject}' and message '{message}'")
    # Here you would add the actual email sending logic using an email service.
    # For example, using Django's send_mail function or an external service API.
    return True

def send_telegram_notification(telegram_id: str, message: str):
    """
    Simulate sending a Telegram notification.
    In a real-world scenario, this would integrate with the Telegram Bot API.
    """
    print(f"Sending Telegram message to {telegram_id}: '{message}'")
    # Here you would add the actual Telegram sending logic using the Telegram Bot API.
    return True