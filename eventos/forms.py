from django import forms
from .models import Event, Dispendio
from django.utils import timezone
from django.forms import inlineformset_factory


class EventForm(forms.ModelForm):

    cep = forms.CharField(
        max_length=9,
        label='CEP',
        widget=forms.TextInput(attrs={
            'inputmode': 'numeric',
            'autocomplete': 'postal-code',
            'placeholder': '00000-000',
            'maxlength': '9',
    })
)

    class Meta:
        model = Event
        fields = "name", "date", "start_time", "end_time", "cep", "location", "number", "complement", "neighborhood", "city", "state", "description",
        widgets = {
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'start_time': forms.TimeInput(format='%H:%M',attrs={'type': 'time'}),
            'end_time': forms.TimeInput(format='%H:%M',attrs={'type': 'time'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['start_time'].input_formats = ['%H:%M']
        self.fields['end_time'].input_formats = ['%H:%M']
        self.fields['date'].widget.attrs['min'] = timezone.localdate().isoformat()

    def clean_date(self):
        date = self.cleaned_data.get('date')
        today = timezone.localdate()
        if date and date < today:
            self.add_error('date', 'A data do evento não pode ser no passado.')
            
        return date
    
    def clean(self):
        cleaned_date = super().clean()
        start_time = cleaned_date.get('start_time')
        end_time = cleaned_date.get('end_time')

        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', 'A hora de término deve ser depois da hora de início.')
        
        return cleaned_date

    def clean_cep(self):
        cep = self.cleaned_data.get('cep', '')

    # Remove hífen, espaços etc.
        cep = ''.join(filter(str.isdigit, cep))

        if len(cep) != 8:
            raise forms.ValidationError(
            'Informe um CEP válido com 8 dígitos.'
        )

        return cep

class EventFilterForm(forms.Form):
    name = forms.CharField(max_length=100, required=False, label='Nome do evento')
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='Data')
    start_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label='Hora de início')
    end_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label='Hora de término')
    location = forms.CharField(max_length=255, required=False, label='Localização')


class DispendioForm(forms.ModelForm):

    class Meta:
        model = Dispendio

        fields = ['descricao_gasto', 'fornecedor', 'valor', 'observacao', 'imagem']

        widgets = {
            
            'descricao_gasto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição do gasto'}),
            'fornecedor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fornecedor'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Valor'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Observação'}),
            'imagem': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*,.pdf,application/pdf',
            }),
        }

DispendioFormSet = inlineformset_factory(
    Event,
    Dispendio,
    form=DispendioForm,
    extra=1,
    can_delete=True
)
