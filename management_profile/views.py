from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, TemplateView, CreateView, FormView, DeleteView, UpdateView
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.conf import settings
from app.decorator import login_required_com_mensagem
from eventos.models import Event
from management_profile.models import Profile

from .models import Profile
from .forms import ProfileForm, ImportProfilesForm, ProfileSearchForm

import pandas as pd
import qrcode
import base64
import re
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader


# Views Básicas
@method_decorator(login_required_com_mensagem, name='dispatch')
class NewProfileView(CreateView):
    model = Profile
    template_name = "new_profile.html"
    form_class = ProfileForm
    success_url = "/list_profile/"

@method_decorator(login_required_com_mensagem, name='dispatch')
class ListProfileView(ListView):
    model = Profile
    template_name = 'list_profile.html'
    context_object_name = 'profiles'

    def get_queryset(self):
        profiles = super().get_queryset().order_by('name')
        search = self.request.GET.get('search')

        if search:
            profiles = profiles.filter(name_icontains=search)

        return profiles

@method_decorator(login_required_com_mensagem, name='dispatch')
class ProfileDetailView(DetailView):
    model = Profile
    template_name = 'profile_detail.html'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.object

        eventos_participados = Event.objects.filter(
            presencas__profile=profile
        ).distinct().order_by('-date', '-start_time')

        context['eventos_participados'] = eventos_participados
        return context

@method_decorator(login_required_com_mensagem, name='dispatch')
class ProfileDeleteView(DeleteView):
    model = Profile
    template_name = 'delete_profile.html'
    success_url = reverse_lazy('list_profile')

@method_decorator(login_required_com_mensagem, name='dispatch')
class ProfileUpdateView(UpdateView):
    model = Profile
    template_name = 'update_profile.html'
    form_class = ProfileForm
    success_url = reverse_lazy('list_profile')

@method_decorator(login_required_com_mensagem, name='dispatch')
class ProfileQrCodeView(TemplateView):
    template_name = 'profile_qrcode.html'

    def get_context_data(self, **kwargs):
        # Método responsável por dar o contexto para o template. Vamos sobreescreve-lo
        context = super().get_context_data(**kwargs)

        profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        # Essa função capturar um profile do banco usando o id passado na url. Se não encontrar, retorna um 404
        
        buffer, profile_url = generate_profile_qr_code(self.request, profile)

        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        context['profile'] = profile
        context['profile_url'] = profile_url
        context['qr_code'] = qr_base64

        # Manda tudo pro contexto do template

        return context

@method_decorator(login_required_com_mensagem, name='dispatch')
class ImportProfilesView(FormView):
    template_name = "import_profiles.html"
    form_class = ImportProfilesForm
    success_url = reverse_lazy("list_profile")

    def form_valid(self, form):
        file = form.cleaned_data["file"]

        # Lê o arquivo
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.name.endswith(".xlsx"):
                df = pd.read_excel(file)
            else:
                form.add_error("file", "Envie um arquivo .csv ou .xlsx")
                return self.form_invalid(form)
        except Exception as e:
            form.add_error("file", f"Erro ao ler o arquivo: {e}")
            return self.form_invalid(form)

        # Normaliza nomes das colunas
        df.columns = df.columns.str.strip().str.lower()

        # Verifica colunas obrigatórias
        required_columns = {"name", "email", "cpf", "role", "phone"}
        if not required_columns.issubset(set(df.columns)):
            missing = required_columns - set(df.columns)
            form.add_error(
                "file",
                f"Colunas obrigatórias ausentes: {', '.join(missing)}"
            )
            return self.form_invalid(form)

        created_count = 0
        updated_count = 0
        errors = []

        # Remove linhas totalmente vazias
        df = df.dropna(how="all")

        # Função para validar CPF
        def validar_cpf(cpf):
            cpf = cpf.replace(".", "").replace("-", "").strip()
            if len(cpf) != 11 or not cpf.isdigit():
                return False
            # Validação do CPF
            if cpf == cpf[0] * 11:  # CPF com todos os números iguais é inválido
                return False
            soma = 0
            for i in range(9):
                soma += int(cpf[i]) * (10 - i)
            resto = soma % 11
            digito1 = 0 if resto < 2 else 11 - resto
            soma = 0
            for i in range(10):
                soma += int(cpf[i]) * (11 - i)
            resto = soma % 11
            digito2 = 0 if resto < 2 else 11 - resto
            return cpf[-2:] == f"{digito1}{digito2}"

        for index, row in df.iterrows():
            line_number = index + 2  # considerando cabeçalho na linha 1
            try:
                name = str(row.get("name", "")).strip()
                email = str(row.get("email", "")).strip()
                cpf = str(row.get("cpf", "")).strip()
                phone = str(row.get("phone", "")).strip()
                role = str(row.get("role", "")).strip()
                if name == "nan":
                    name = ""
                if email == "nan":
                    email = ""
                if cpf == "nan":
                    cpf = ""
                if phone == "nan":
                    phone = ""

                # Normaliza e valida CPF
                cpf = cpf.replace(".", "").replace("-", "").strip()

                if not name or not email or not cpf or not phone:
                    errors.append(f"Linha {line_number}: dados incompletos.")
                    continue

                if not validar_cpf(cpf):
                    errors.append(f"Linha {line_number}: CPF inválido.")
                    continue

                # Normaliza o telefone (apenas números)
                phone = re.sub(r'\D', '', phone)  # Remove qualquer caractere não numérico

                # Cria ou atualiza o perfil
                obj, created = Profile.objects.update_or_create(
                    cpf=cpf,
                    defaults={
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "role": role,
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                errors.append(f"Linha {line_number}: {str(e)}")

        messages.success(
            self.request,
            f"Importação concluída. Criados: {created_count} | Atualizados: {updated_count}"
        )

        if errors:
            messages.warning(
                self.request,
                "Ocorreram erros em algumas linhas: " + " | ".join(errors[:5])
            )

        return super().form_valid(form)

#Funções comuns
def generate_profile_qr_code(request, profile):
    # Função responsável por gerar o QR code do perfil.
    # Recebe o request quando chamado por uma view,
    # mas também funciona sem request (ex: envio de e-mail).

    profile_path = reverse(
        'profile_detail',
        kwargs={'pk': profile.pk}
    )

    if request:
        profile_url = request.build_absolute_uri(profile_path)
    else:
        profile_url = (
            f"{settings.SITE_URL}{profile_path}"
        )

    qr = qrcode.make(profile_url)

    buffer = BytesIO()
    qr.save(buffer, format='PNG')

    buffer.seek(0)

    return buffer, profile_url

def generate_profile_pdf(request, profiles):
    # Função para gerar um PDF com a lista de perfis. (qrcode).

    response = HttpResponse(content_type='application/pdf')
    # Cria a resposta HTTP informando que o conteúdo é um PDF.
    response['Content-Disposition'] = 'attachment; filename="Crachas_perfis.pdf"'
    # attachment faz com que o navegador baixe o arquivo ao invés de exibir.
    # Filename define o nome do arquivo que será baixado.

    pdf_buffer = BytesIO()
    # Cria um buffer (Arquivo temporário) na memória para armazenar o PDF enquanto é gerado.

    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    # Cria um objeto canvas do ReportLab, que é usado para desenhar o conteúdo do PDF. Define o tamanho da página como A4.


    page_width, page_height = A4
    # Captura a largura e altura da página A4 para ajudar no posicionamento dos elementos.

    # Margem do documento (1cm = 28.35 pontos)
    margin = 28.35

    usable_width = page_width - (2 * margin)
    # Calcula a largura útil da página subtraindo as margens.

    usable_hight = page_height - (2 * margin)
    
    cols = 3
    rows = 3
    # Define o número de colunas e linhas para organizar os crachás na página.

    gap_x = 18
    gap_y = 18
    # Calcula o espaço entre os crachás. gap_x é a distância horizontal entre eles, e gap_y é a distância vertical.

    card_width = (usable_width - (gap_x * (rows - 1))) / rows
    card_height = (usable_hight - (gap_y * (cols - 1))) / cols
    # Calcula a largura e altura de cada crachá, levando em conta o espaço entre eles.

    card_colors = [HexColor("#0C97B2"), HexColor("#21B6D4"), HexColor("#0C97B2")]
    # Define uma paleta de cores para os crachás, usando tons de azul.

    def draw_wrapped_name(text, center_x, start_y, max_width, font_name="Helvetica-Bold"):
        # Função auxiliar para desenhar o nome do perfil, quebrando em múltiplas linhas se necessário.
        font_size = 16
        # Tamanho inicial da fonte
        min_font_size = 10
        # Tamanho mínimo da fonte para evitar que fique ilegível
        words = text.split()
        # Divide o nome em palavras para facilitar a quebra de linha

        while font_size >= min_font_size:
            # Enquanto o tamanho da fonte for maior ou igual ao mínimo, tenta ajustar o texto.
            lines = []
            # Vai guardar as linhas finais do texto
            current_line = ""
            # Linha atual que está sendo construída

            for word in words:
                test = f'{current_line} {word}'.strip()
                # Testa adicionar a próxima palavra à linha atual
                if stringWidth(test, font_name, font_size) <= max_width:
                    current_line = test
                    # Essa função calcula a largura do texto com a fonte e tamanho atuais. Se couber, adiciona a palavra à linha.
                else:
                    if current_line:
                        # Caso não caiba, adiciona a linha atual à lista de linhas e começa uma nova linha com a palavra.
                        lines.append(current_line)
                    current_line = word
            if current_line:
                # Adiciona a última linha restante
                lines.append(current_line)
            if len(lines) <= 2:
                c.setFillColor(black)
                # Define a cor do texto como preto
                c.setFont(font_name, font_size)
                # Define a fonte e o tamanho para desenhar o texto
                line_height = font_size + 2
                # Calcula a distância entre as linhas.
                total_height = len(lines) * line_height
                # Calcula a altura total do bloco de texto para centralizar verticalmente.
                y = start_y + (total_height / 2) - line_height + 4
                # Ajusta a posição vertical para centralizar o texto dentro do crachá.

                for line in lines:
                    c.drawCentredString(center_x, y, line)
                    y -= line_height
                # Desenha cada linha do nome centralizada horizontalmente e ajusta a posição vertical para a próxima linha.
                
                return
            font_size -= 1
            # Se o texto não couber em 2 linhas, reduz o tamanho da fonte e tenta novamente. Isso garante que o nome caiba no crachá mesmo que seja longo.

        # Se nem com a fonte 10 couber, desenha só os 30 primeiros caracteres.
        c.setFillColor(black)
        c.setFont(font_name, 10)
        c.drawCentredString(center_x, start_y, text[:30])

    for index, profile in enumerate(profiles):
        page_index = index % 9
        # Define a posição do crachá na página (0 a 8) para organizar em 3x3.

        if index > 0 and page_index == 0:
            c.showPage()
            # Se já tiver desenhado 9 crachás, inicia uma nova página.
        
        row = page_index // cols
        col = page_index % cols
        # Calcula em qual linha o cracha deve ser desenhado (0, 1 ou 2) e em qual coluna (0, 1 ou 2).

        x = margin + col * (card_width + gap_x)
        # Calcula a posição horizontal do crachá com base na coluna, largura do crachá e espaço entre eles.
        y = page_height - margin - ((row +1) * card_height) - (row * gap_y)
        # Calcula a posição vertical do crachá com base na linha, altura do crachá e espaço entre eles.

        #Fundo do crachá
        c.setFillColor(card_colors[col % len(card_colors)])
        # Define a cor de preenchimento para o fundo do crachá, alternando entre as cores definidas na paleta.
        c.rect(x, y, card_width, card_height, fill=1, stroke=0)
        # Desenha um retângulo preenchido para o fundo do crachá na posição calculada.

        qr_buffer, profile_url = generate_profile_qr_code(request, profile)
        # Gera o QR code para o perfil atual e obtém o buffer de imagem e a URL do perfil.

        qr_reader = ImageReader(qr_buffer)
        # Cria um objeto ImageReader a partir do buffer do QR code para poder desenhá-lo no PDF.

        qr_size = min(card_width * 0.62, card_height * 0.48)
        # Define o tamanho do QR code, garantindo que ele caiba dentro do crachá com uma margem.

        qr_x = x + (card_width - qr_size) / 2
        qr_y = y + card_height *0.43
        # Calcula a posição do QR code para centralizá-lo horizontalmente.

        c.drawImage(
            qr_reader,
            qr_x,
            qr_y,
            width=qr_size,
            height=qr_size,
            preserveAspectRatio=True,
            # Mantém a proporção do QR code para evitar distorções, mesmo que o tamanho seja ajustado para caber no crachá.
            mask='auto'
            # Trata transparência automaticamente.
        )

        name_center_x = x + (card_width / 2)
        # Calcula a posição horizontal central para o nome do perfil, garantindo que ele fique centralizado no crachá.
        name_center_y = y + (card_height * 0.25)
        # Calcula a posição vertical para o nome do perfil, posicionando-o na parte superior do crachá, acima do QR code.
        text_max_width = card_width - 24
        # Define a largura máxima para o texto do nome, deixando uma margem de 12 pontos de cada lado para evitar que o texto fique muito próximo das bordas do crachá.

        draw_wrapped_name(
            profile.name,
            name_center_x,
            name_center_y,
            text_max_width
        )
        # Chama a função auxiliar para desenhar o nome do perfil, passando o texto, as posições centrais e a largura máxima para garantir que o nome seja exibido corretamente no crachá, mesmo que seja longo.
    c.save()

    pdf_value = pdf_buffer.getvalue()
    # Pega os bytes do pdf
    pdf_buffer.close()
    # Fecha o buffer de memória
    response.write(pdf_value)
    # Escrve os bytes do PDF na resposta HTTP para que o navegador possa baixar o arquivo.
    return response
    
def build_profile_filters(form):
    filters = {}

    if form.is_valid():
        if form.cleaned_data['name']:
            filters['name__icontains'] = form.cleaned_data['name']
        if form.cleaned_data['cpf']:
            filters['cpf__icontains'] = form.cleaned_data['cpf']
        if form.cleaned_data['email']:
            filters['email__icontains'] = form.cleaned_data['email']
        if form.cleaned_data['role']:
            filters['role'] = form.cleaned_data['role']
        if form.cleaned_data['phone']:
            filters['phone__icontains'] = form.cleaned_data['phone']

        profiles = Profile.objects.filter(**filters).order_by('name')
        
    else:
        profiles = Profile.objects.all().order_by('name')

    return form, profiles

#Views de download de QR code
@login_required_com_mensagem
def download_profiles_qr_code_view(request):
    # View para baixar o PDF com os QR codes de todos os perfis. Ele chama a função de geração de PDF passando a lista completa de perfis.
    profiles = Profile.objects.all().order_by('name')
    response = generate_profile_pdf(request, profiles=profiles)
    return response

@login_required_com_mensagem
def download_profile_qr_code_view(request, pk):
    # View para baixar o PDF do perfil específico. Ele chama a função de geração de PDF passando apenas o perfil selecionado.
    profile = get_object_or_404(Profile, pk=pk)
    response = generate_profile_pdf(request, profiles=[profile])

    return response

@login_required_com_mensagem
def AdvanceSearchProfileView(request):
    form = ProfileSearchForm(request.GET)
    form, profiles = build_profile_filters(form)

    if form.cleaned_data.get('download'):
        if form.cleaned_data['download'] == 'yes':
            response = generate_profile_pdf(request, profiles=profiles)
            return response


    return render(request, 'advance_search_profile.html', {'form': form, 'profiles': profiles})







