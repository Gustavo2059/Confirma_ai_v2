from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import Event
from .services.email_services import notify_users_new_event


@receiver(
    post_save,
    sender=Event,
    dispatch_uid="eventos.notify_when_event_created"
)
def notify_when_event_created(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: notify_users_new_event(instance))
