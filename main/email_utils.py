from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from django.utils.html import strip_tags

def send_signup_email(user):
    """Sends a welcome email to a new user."""
    subject = 'Welcome to Capital Finance!'
    context = {
        'user': user,
        'username': user.username,
    }
    
    # Render HTML; fall back to a plain-text version built from HTML if txt template missing
    html_message = render_to_string('emails/signup_email.html', context)
    try:
        plain_message = render_to_string('emails/signup_email.txt', context)
    except TemplateDoesNotExist:
        plain_message = strip_tags(html_message)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email, "standardcapitalfinanceorg@gmail.com"]
    
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

def send_deposit_email(user, transaction):
    """Sends an email notification for a successful deposit."""
    subject = 'Deposit Confirmation'
    # Support either 'currency' or legacy 'coin_type' field
    coin_type = getattr(transaction, 'currency', None) or getattr(transaction, 'coin_type', None)
    context = {
        'user': user,
        'username': user.username,
        'transaction': transaction,
        'amount': transaction.amount,
        'coin_type': coin_type,
    }

    html_message = render_to_string('emails/deposit_email.html', context)
    try:
        plain_message = render_to_string('emails/deposit_email.txt', context)
    except TemplateDoesNotExist:
        plain_message = strip_tags(html_message)

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email, "standardcapitalfinanceorg@gmail.com"]
    
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

def send_withdrawal_email(user, transaction):
    """Sends an email notification for a withdrawal request."""
    subject = 'Withdrawal Request Received'
    coin_type = getattr(transaction, 'currency', None) or getattr(transaction, 'coin_type', None)
    context = {
        'user': user,
        'username': user.username,
        'transaction': transaction,
        'amount': transaction.amount,
        'coin_type': coin_type,
    }

    html_message = render_to_string('emails/withdrawal_email.html', context)
    try:
        plain_message = render_to_string('emails/withdrawal_email.txt', context)
    except TemplateDoesNotExist:
        plain_message = strip_tags(html_message)

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email, "standardcapitalfinanceorg@gmail.com"]
    
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)