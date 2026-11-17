from django import forms
from .models import Profile
from phonenumber_field.formfields import PhoneNumberField
import re

def validate_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    # Remove tudo que não for número
    # .sub é um método que substitui todas as ocorrências por um determinado valor.
    if len(cpf) != 11:
        return False
    
    if cpf == cpf[0] * 11:
        # Elimina CPFs com todos os números iguais
        return False
    
    soma = 0
    for i in range(9):
        # Validação do primeiro dígito verificador
        soma += int(cpf[i]) * (10 - i)

    resto = (soma * 10) % 11

    if resto == 10:
        resto = 0

    if resto != int(cpf[9]):
        return False

    # Validação do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)

    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0

    if resto != int(cpf[10]):
        return False

    return True

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        verification = validate_cpf(cpf)
        if not verification:
            raise forms.ValidationError("CPF inválido.")
        return re.sub(r'\D', '', cpf)

#importa um arquivo CSV para upload em massa. 
class ImportProfilesForm(forms.Form):
    file = forms.FileField(label="Selecione um arquivo CSV ou XLSX")

class ProfileSearchForm(forms.Form):
    name = forms.CharField(max_length=100, label="Nome", required=False)
    cpf = forms.CharField(max_length=11, label="CPF", required=False)
    email = forms.EmailField(max_length=100, label="Email", required=False)
    role = forms.CharField(max_length=100, label='Cargo', required=False)
    phone = PhoneNumberField(widget=forms.TextInput(attrs={'placeholder': 'Digite o telefone com DDD'}), required=False)
    download = forms.ChoiceField(choices=[('', 'Selecione uma opção'), ('yes', 'Sim'), ('no', 'Não')], label="Escolha uma opção", required=False)