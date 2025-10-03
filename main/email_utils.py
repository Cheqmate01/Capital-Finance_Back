from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def send_signup_email(user):
    """Sends a welcome email to a new user."""
    subject = 'Welcome to Capital Finance!'
    context = {'username': user.username}
    
    # Render both HTML and plain text versions of the email
    html_message = render_to_string('./templates/emails/signup_email.html', context)
    plain_message = render_to_string('./templates/emails/signup_email.txt', context)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email, "standardcapitalfinanceorg@gmail.com"]
    
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

def send_deposit_email(user, transaction):
    """Sends an email notification for a successful deposit."""
    subject = 'Deposit Confirmation'
    context = {
        'username': user.username,
        'amount': transaction.amount,
        'coin_type': transaction.coin_type
    }

    html_message = render_to_string('./templates/emails/deposit_email.html', context)
    plain_message = render_to_string('./templates/emails/deposit_email.txt', context)

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email, "standardcapitalfinanceorg@gmail.com"]
    
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

def send_withdrawal_email(user, transaction):
    """Sends an email notification for a withdrawal request."""
    subject = 'Withdrawal Request Received'
    context = {
        'username': user.username,
        'amount': transaction.amount,
        'coin_type': transaction.coin_type
    }

    html_message = render_to_string('./templates/emails/withdrawal_email.html', context)
    plain_message = render_to_string('./templates/emails/withdrawal_email.txt', context)

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email, "standardcapitalfinanceorg@gmail.com"]
    
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)