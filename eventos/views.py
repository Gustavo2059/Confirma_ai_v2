from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.http import HttpResponse
from django.db import transaction
from django.shortcuts import redirect
from django.db.models import Sum
from django.conf import settings


from app.decorator import login_required_com_mensagem
from management_profile.models import Profile
from .models import Event, Presenca, Dispendio
from .forms import EventForm, EventFilterForm, DispendioForm, DispendioFormSet

import json
import re
import csv
import base64
import urllib.error
import urllib.request

@method_decorator(login_required_com_mensagem, name='dispatch')
class HomeEventView(ListView):
    model = Event
    template_name = "home_event.html"
    context_object_name = "events"
    paginate_by = 3


    def get_queryset(self):
        return Event.objects.all().order_by('date')

@method_decorator(login_required_com_mensagem, name='dispatch')
class NewEventView(CreateView):
    model = Event
    template_name = "new_event.html"
    form_class = EventForm
    success_url = "/list_event/"


@method_decorator(login_required_com_mensagem, name='dispatch')
class ListEventView(ListView):
    model = Event
    template_name = "list_event.html"
    context_object_name = "events"

    def get_queryset(self):
        return Event.objects.all().order_by('date')


@method_decorator(login_required_com_mensagem, name='dispatch')
class DetailEventView(DetailView):
    model = Event
    template_name = "detail_event.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        dispendios = self.object.dispendios.all().order_by('-criado_em')
        context['dispendios'] = dispendios

        context['total_dispendios'] = dispendios.aggregate(total=Sum('valor'))['total'] or 0

        return context


@method_decorator(login_required_com_mensagem, name='dispatch')
class UpdateEventView(UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'update_event.html'

    def get_success_url(self):
        return reverse_lazy('detail_event', kwargs={'pk': self.object.pk})


@method_decorator(login_required_com_mensagem, name='dispatch')
class DeleteEventView(DeleteView):
    model = Event
    template_name = 'delete_event.html'
    success_url = reverse_lazy('list_event')

@login_required_com_mensagem
def AdvanceSearchEventView(request):
    form = EventFilterForm(request.GET)
    filters = {}
    # A ideia é criar um dicionário com os filtros que o usuário preencher no formulário.

    if form.is_valid():
        if form.cleaned_data['name']:
            filters['name__icontains'] = form.cleaned_data['name']
        if form.cleaned_data['date']:
            filters['date'] = form.cleaned_data['date']
        if form.cleaned_data['start_time']:
            filters['start_time__exact'] = form.cleaned_data['start_time']
            # Aplica o filtro de hora exata para a hora de início
        if form.cleaned_data['end_time']:
            filters['end_time__exact'] = form.cleaned_data['end_time']
            # Aplica o filtro de hora exata para a hora de término
        if form.cleaned_data['location']:
            filters['location__icontains'] = form.cleaned_data['location']

        events = Event.objects.filter(**filters).order_by('name')

    else: 
        events = Event.objects.all().order_by('name')

    return render(request, 'advance_search_event.html', {'form': form, 'events': events})


@login_required_com_mensagem
def scanner_evento(request, evento_id):
    evento = get_object_or_404(Event, pk=evento_id)
    return render(request, 'scanner_evento.html', {'evento': evento})


@login_required_com_mensagem
def registrar_presenca(request, evento_id):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Método não permitido."
        }, status=405)

    try:
        data = json.loads(request.body)
        qr_code = data.get("qr_code")

        if not qr_code:
            return JsonResponse({
                "success": False,
                "message": "QR Code não informado."
            }, status=400)

        evento = get_object_or_404(Event, pk=evento_id)

        match = re.search(r'/profile/(\d+)/?$', qr_code)

        if not match:
            return JsonResponse({
                "success": False,
                "message": f"QR Code inválido: {qr_code}"
            }, status=400)

        profile_id = match.group(1)
        profile = Profile.objects.filter(pk=profile_id).first()

        if not profile:
            return JsonResponse({
                "success": False,
                "message": f"Perfil não encontrado para o ID {profile_id}."
            }, status=404)

    
        presenca, created = Presenca.objects.get_or_create(
            evento=evento,
            profile=profile
        )

        nome = getattr(profile, 'name', None) or getattr(profile, 'nome', None) or str(profile)

        if created:
            return JsonResponse({
                "success": True,
                "message": f"Presença registrada para {nome}."
            })

        return JsonResponse({
            "success": False,
            "message": f"{nome} já teve presença registrada neste evento."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)
    

@login_required_com_mensagem
def listar_presencas_evento(request, evento_id):
    evento = get_object_or_404(Event, pk=evento_id)
    presencas = Presenca.objects.filter(evento=evento).select_related('profile').order_by('-data_hora')

    return render(request, 'listar_presencas_evento.html', {
        'evento': evento,
        'presencas': presencas
    })

#Exportar presenças para CSV
@login_required_com_mensagem
def exportar_presencas_csv(request, evento_id):
    evento = get_object_or_404(Event, pk=evento_id)
    presencas = Presenca.objects.filter(evento=evento).select_related('profile').order_by('data_hora')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Presencas_evento_{evento.id}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Participante', 'E-mail', 'Data', 'Hora'])

    for presenca in presencas:
        profile = presenca.profile

        nome = getattr(profile, 'name', None) or getattr(profile, 'nome', None) or str(profile)
        email = getattr(profile, 'email', '')

        data_local = timezone.localtime(presenca.data_hora)

        data = data_local.strftime('%d/%m/%Y')
        hora = data_local.strftime('%H:%M:%S')

        writer.writerow([nome, email, data, hora])

    return response




@method_decorator(login_required_com_mensagem, name='dispatch')
class NewDispendioView(View):

    template_name = "dispendio.html"


    def get(self, request, pk=None, *args, **kwargs):

        evento = None


        if pk:
            evento = get_object_or_404(
                Event,
                pk=pk
            )


        formset = DispendioFormSet(
            instance=evento,
            prefix='form'
        )


        context = {
            'evento': evento,
            'eventos': Event.objects.all().order_by('date'),
            'formset': formset,
        }


        return render(
            request,
            self.template_name,
            context
        )



    def post(self, request, pk=None, *args, **kwargs):

        if pk:

            evento = get_object_or_404(
                Event,
                pk=pk
            )


        else:

            evento_id = request.POST.get(
                'evento_global'
            )

            if not evento_id:

                formset = DispendioFormSet(
                    request.POST,
                    prefix='form'
                )

                return render(
                    request,
                    self.template_name,
                    {
                        'evento': None,
                        'eventos': Event.objects.all().order_by('date'),
                        'formset': formset,
                        'evento_error': 'Selecione um evento.'
                    }
                )


            evento = get_object_or_404(
                Event,
                pk=evento_id
            )


        formset = DispendioFormSet(
            request.POST,
            request.FILES,
            instance=evento,
            prefix='form'
        )


        if formset.is_valid():

            with transaction.atomic():

                formset.save()


            return redirect(
                'detail_event',
                pk=evento.pk
            )


        return render(
            request,
            self.template_name,
            {
                'evento': evento,
                'eventos': Event.objects.all().order_by('date'),
                'formset': formset,
            }
        )

@login_required_com_mensagem
def analisar_nota_fiscal(request):
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido.'}, status=405)

    imagem = request.FILES.get('imagem')
    if not imagem:
        return JsonResponse({'erro': 'Selecione uma imagem da nota fiscal.'}, status=400)

    tipos_permitidos = {
        'image/jpeg',
        'image/png',
        'image/webp',
        'image/gif',
        'application/pdf',
    }
    if imagem.content_type not in tipos_permitidos:
        return JsonResponse({'erro': 'Envie uma imagem JPG, PNG, WEBP, GIF ou um PDF.'}, status=400)

    if imagem.size > 10 * 1024 * 1024:
        return JsonResponse({'erro': 'A imagem deve ter no máximo 10 MB.'}, status=400)

    if not settings.OPENAI_API_KEY:
        return JsonResponse({'erro': 'A chave da API de IA não está configurada.'}, status=503)

    imagem_base64 = base64.b64encode(imagem.read()).decode('ascii')
    data_url = f'data:{imagem.content_type};base64,{imagem_base64}'
    arquivo_entrada = (
        {
            'type': 'input_file',
            'filename': imagem.name,
            'file_data': data_url,
        }
        if imagem.content_type == 'application/pdf'
        else {
            'type': 'input_image',
            'image_url': data_url,
            'detail': 'high',
        }
    )
    schema = {
        'type': 'object',
        'properties': {
            'fornecedor': {'type': 'string'},
            'itens': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'descricao': {'type': 'string'},
                        'valor': {'type': 'number'},
                        'observacao': {'type': 'string'},
                    },
                    'required': ['descricao', 'valor', 'observacao'],
                    'additionalProperties': False,
                },
            },
        },
        'required': ['fornecedor', 'itens'],
        'additionalProperties': False,
    }
    payload = {
        'model': settings.OPENAI_INVOICE_MODEL,
        'store': False,
        'instructions': (
            'Extraia os itens desta nota fiscal brasileira. Gere uma linha por item. '
            'Use o valor total da linha, considerando quantidade, e não o valor unitário. '
            'Não inclua subtotal, total, troco, impostos ou formas de pagamento como itens. '
            'Na observação, registre quantidade e unidade quando estiverem legíveis. '
            'Não invente dados ilegíveis; use texto vazio quando necessário.'
        ),
        'input': [{
            'role': 'user',
            'content': [
                {'type': 'input_text', 'text': 'Analise esta nota fiscal e separe cada dispêndio.'},
                arquivo_entrada,
            ],
        }],
        'text': {'format': {
            'type': 'json_schema',
            'name': 'itens_nota_fiscal',
            'strict': True,
            'schema': schema,
        }},
    }
    requisicao = urllib.request.Request(
        'https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(requisicao, timeout=60) as resposta:
            resultado = json.loads(resposta.read().decode('utf-8'))

        texto = next(
            conteudo['text']
            for saida in resultado.get('output', [])
            if saida.get('type') == 'message'
            for conteudo in saida.get('content', [])
            if conteudo.get('type') == 'output_text'
        )
        dados = json.loads(texto)
        if not dados.get('itens'):
            return JsonResponse({'erro': 'Nenhum item legível foi encontrado na nota.'}, status=422)
        return JsonResponse(dados)
    except StopIteration:
        return JsonResponse({'erro': 'A IA não retornou itens válidos.'}, status=502)
    except (json.JSONDecodeError, KeyError, TypeError):
        return JsonResponse({'erro': 'A resposta da IA não pôde ser interpretada.'}, status=502)
    except urllib.error.HTTPError as erro:
        status = 429 if erro.code == 429 else 502
        mensagem = (
            'Limite da API de IA atingido. Tente novamente em instantes.'
            if erro.code == 429
            else 'Não foi possível analisar a nota fiscal agora.'
        )
        return JsonResponse({'erro': mensagem}, status=status)
    except (urllib.error.URLError, TimeoutError):
        return JsonResponse({'erro': 'O serviço de IA está indisponível.'}, status=503)


@login_required_com_mensagem
def carregar_dispendios(request, evento_id):

    evento = get_object_or_404(
        Event,
        pk=evento_id
    )

    dispendios = evento.dispendios.all().order_by('criado_em', 'pk')


    dados = []

    for d in dispendios:

        dados.append({

            "id": d.id,

            "descricao": d.descricao_gasto,

            "fornecedor": d.fornecedor,

            "valor": str(d.valor),

            "observacao": d.observacao,

            "imagem": d.imagem.url if d.imagem else None

        })


    return JsonResponse(
        {
            "evento": evento.name,
            "dispendios": dados
        }
    )
