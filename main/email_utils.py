
from django.core.mail import send_mail
from django.conf import settings

def send_signup_email(user):
    """Sends a welcome email to a new user."""
    subject = 'Welcome to Capital Finance!'
    message = f'Hi {user.username},\n\nThank you for registering at Capital Finance. We are excited to have you with us.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)

def send_deposit_email(user, transaction):
    """Sends an email notification for a successful deposit."""
    subject = 'Deposit Confirmation'
    message = f'Hi {user.username},\n\nYour deposit request of {transaction.amount} {transaction.coin_type} has been successfully received and is being processed.\n\nYour new balance will be updated shortly.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)

def send_withdrawal_email(user, transaction):
    """Sends an email notification for a withdrawal request."""
    subject = 'Withdrawal Request Received'
    message = f'Hi {user.username},\n\nWe have received your withdrawal request for {transaction.amount} {transaction.coin_type}. It is being processed.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)
