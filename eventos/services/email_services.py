from datetime import datetime, timedelta, timezone as dt_timezone
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

from email.mime.image import MIMEImage
from management_profile.views import generate_profile_qr_code

from management_profile.models import Profile
from eventos.models import EventEmailDelivery


def format_cep(cep):
    """
    Formata o CEP para o padrão 00000-000.
    """
    if not cep:
        return ""

    cep = str(cep).replace("-", "").replace(".", "").strip()

    if len(cep) == 8 and cep.isdigit():
        return f"{cep[:5]}-{cep[5:]}"

    return cep


def build_event_address(event, include_complement=False):
    """
    Monta o endereço completo do evento.

    Para o Google Agenda/Maps:
    include_complement=False

    Para exibição no e-mail:
    include_complement=True
    """

    parts = []

    # Logradouro + número
    if event.location:
        street = event.location.strip()

        if event.number:
            street += f", {str(event.number).strip()}"

        parts.append(street)

    # Bairro
    if event.neighborhood:
        parts.append(event.neighborhood.strip())

    # Cidade + UF
    city_state = ""

    if event.city:
        city_state = event.city.strip()

    if event.state:
        state = event.state.strip().upper()

        if city_state:
            city_state += f" - {state}"
        else:
            city_state = state

    if city_state:
        parts.append(city_state)

    # CEP
    if event.cep:
        cep = format_cep(event.cep)

        if cep:
            parts.append(f"CEP {cep}")

    # País ajuda o Google Maps a localizar corretamente
    if parts:
        parts.append("Brasil")

    full_address = ", ".join(parts)

    # Complemento somente quando solicitado
    if include_complement and event.complement:
        complement = event.complement.strip()

        if full_address:
            full_address += f" - Complemento: {complement}"
        else:
            full_address = f"Complemento: {complement}"

    return full_address


def build_google_calendar_link(event):
    # Só gera o link se tiver data + hora inicial + hora final
    if not event.date or not event.start_time or not event.end_time:
        return None

    start_dt = datetime.combine(
        event.date,
        event.start_time
    )

    end_dt = datetime.combine(
        event.date,
        event.end_time
    )

    tz = timezone.get_default_timezone()

    if timezone.is_naive(start_dt):
        start_dt = timezone.make_aware(
            start_dt,
            tz
        )

    if timezone.is_naive(end_dt):
        end_dt = timezone.make_aware(
            end_dt,
            tz
        )

    # Caso o evento termine depois da meia-noite
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    start_utc = start_dt.astimezone(
        dt_timezone.utc
    )

    end_utc = end_dt.astimezone(
        dt_timezone.utc
    )

    # Endereço otimizado para Google Agenda / Google Maps
    google_address = build_event_address(
        event,
        include_complement=False
    )

    # Monta os detalhes que aparecerão no Google Agenda
    details_parts = []

    if event.description:
        details_parts.append(event.description.strip())

    if event.complement:
        details_parts.append(
            f"Complemento: {event.complement.strip()}"
        )

    details = "\n\n".join(details_parts)

    params = {
        "action": "TEMPLATE",
        "text": event.name,
        "dates": (
            f"{start_utc.strftime('%Y%m%dT%H%M%SZ')}/"
            f"{end_utc.strftime('%Y%m%dT%H%M%SZ')}"
        ),
        "details": details,
        "location": google_address,
        "ctz": settings.TIME_ZONE,
    }

    return (
        "https://calendar.google.com/calendar/render?"
        + urlencode(params)
    )


def notify_users_new_event(event):
    profiles = Profile.objects.exclude(
        email__isnull=True
    ).exclude(
        email__exact=""
    )

    if not profiles.exists():
        return

    calendar_link = build_google_calendar_link(event)

    subject = f"Novo evento criado: {event.name}"

    # Endereço completo para aparecer no e-mail
    email_address = build_event_address(
        event,
        include_complement=True
    )

    for profile in profiles:
        with transaction.atomic():
            delivery, _ = (
                EventEmailDelivery.objects
                .select_for_update()
                .get_or_create(event=event, profile=profile)
            )

            if delivery.sent_at:
                continue

            buffer, profile_url = generate_profile_qr_code(None, profile)

            context = {
                "profile": profile,
                "event": event,
                "profile_url": profile_url,
                "calendar_link": calendar_link,
                "date_formatted": (
                    event.date.strftime("%d/%m/%Y")
                    if event.date else "Não informado"
                ),
                "start_time_formatted": (
                    event.start_time.strftime("%H:%M")
                    if event.start_time else "Não informado"
                ),
                "end_time_formatted": (
                    event.end_time.strftime("%H:%M")
                    if event.end_time else "Não informado"
                ),
                "location": email_address or "Não informado",
                "description": event.description or "Não informado",
            }

            html_message = render_to_string(
                "emails/new_event_email.html",
                context
            )
            plain_message = strip_tags(html_message)

            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[profile.email],
            )
            email.attach_alternative(html_message, "text/html")

            qr_image = MIMEImage(buffer.getvalue(), _subtype="png")
            qr_image.add_header("Content-ID", "<qr_code>")
            qr_image.add_header(
                "Content-Disposition",
                "inline",
                filename="qr_code.png"
            )
            email.attach(qr_image)
            email.send(fail_silently=False)

            delivery.sent_at = timezone.now()
            delivery.save(update_fields=["sent_at"])
