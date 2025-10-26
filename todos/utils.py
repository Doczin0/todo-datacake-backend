from django.core.mail import send_mail

def send_email(subject, message, to_email):
    # Em DEV com EMAIL_BACKEND=console isso imprime no terminal.
    send_mail(subject, message, None, [to_email], fail_silently=False)
