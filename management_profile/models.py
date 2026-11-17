from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Profile(models.Model):
    name = models.CharField(max_length=100)
    cpf = models.CharField(max_length=11, unique=True)
    email = models.EmailField(unique=True, blank=False, null=False)
    role = models.CharField(max_length=100, blank=True, null=True)
    phone = PhoneNumberField(region='BR', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.email}"