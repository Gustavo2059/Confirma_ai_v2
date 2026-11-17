import uuid

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):

    first_name = forms.CharField(required=True,label="Nome",max_length=150)
    last_name = forms.CharField(required=True,label="Sobrenome",max_length=150)
    email = forms.EmailField(required=True,label="E-mail")

    class Meta:
        model = User

        # Username NÃO aparece mais no formulário
        fields = ('first_name','last_name','email','password1','password2',)

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Este e-mail já está cadastrado."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        # Garante os dados normalizados
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"].strip().lower()

        # Username interno.
        # O usuário nunca precisará digitar ou conhecer esse valor.
        while True:
            internal_username = f"user_{uuid.uuid4().hex[:16]}"

            if not User.objects.filter(
                username=internal_username
            ).exists():
                break

        user.username = internal_username

        if commit:
            user.save()

        return user