import secrets

from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from ..models import MFAChallenge


MFA_EXPIRATION_MINUTES = 10



def send_mfa_email(user, code):

    subject = "Seu código de acesso"


    html_content = render_to_string(
        "emails/mfa_code.html",
        {
            "code": code,
            "expiration": MFA_EXPIRATION_MINUTES,
        }
    )


    text_content = (
        f"Seu código de verificação é: {code}\n\n"
        f"Ele expira em {MFA_EXPIRATION_MINUTES} minutos.\n\n"
        "Se você não tentou entrar, ignore este e-mail."
    )


    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=None,
        to=[user.email],
    )


    email.attach_alternative(
        html_content,
        "text/html"
    )


    email.send()



def create_mfa_challenge(user):

    # Invalida códigos antigos
    MFAChallenge.objects.filter(
        user=user,
        used=False
    ).update(
        used=True
    )


    # Gera código de 6 dígitos
    code = f"{secrets.randbelow(1_000_000):06d}"


    # DEBUG TEMPORÁRIO
    print("==========================")
    print("CÓDIGO MFA GERADO:", code)
    print("==========================")


    challenge = MFAChallenge.objects.create(
        user=user,

        # Salva somente o hash
        code_hash=make_password(code),

        expires_at=timezone.now() + timedelta(
            minutes=MFA_EXPIRATION_MINUTES
        ),

        attempts=0,

        used=False,
    )


    send_mfa_email(
        user,
        code
    )


    return challenge