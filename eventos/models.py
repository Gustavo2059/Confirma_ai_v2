from django.db import models
from management_profile.models import Profile


class Event(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField(blank=False, null=False)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    
    #Endereços
    cep = models.CharField(max_length=8, blank=True, null=True, verbose_name='CEP')
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name='Endereço')
    number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Número')
    description = models.TextField(blank=True, null=True)
    complement = models.CharField(max_length=255, blank=True, null=True, verbose_name='Complemento')
    neighborhood = models.CharField(max_length=255, blank=True, null=True, verbose_name='Bairro')
    city = models.CharField(max_length=255, blank=True, null=True, verbose_name='Cidade')
    state = models.CharField(max_length=255, blank=True, null=True, verbose_name='UF')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class EventEmailDelivery(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="email_deliveries"
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="event_email_deliveries"
    )
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "profile"],
                name="unique_event_email_per_profile"
            )
        ]


class Presenca(models.Model):
    evento = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='presencas')
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='presencas',
        null=True,
        blank=True
    )
    data_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.profile} - {self.evento}'


class Dispendio(models.Model):
    evento = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='dispendios')
    descricao_gasto = models.CharField(max_length=255, blank=False, null=False)
    fornecedor = models.CharField(max_length=255, blank=False, null=False)
    valor = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    observacao = models.TextField(blank=True, null=True)
    imagem = models.FileField(upload_to='dispendios/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.descricao_gasto} - {self.fornecedor} - {self.valor}'
        
