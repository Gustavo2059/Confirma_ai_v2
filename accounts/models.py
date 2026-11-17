from django.conf import settings
from django.db import models


class MFAChallenge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    code_hash = models.CharField(max_length=128)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    attempts = models.PositiveSmallIntegerField(default=0)

    used = models.BooleanField(default=False)

    def __str__(self):
        return f"MFA - {self.user} - {self.created_at}"