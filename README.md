# Confirma Eventos

Sistema web para cadastro de participantes, organização de eventos e controle de presença por QR Code. O projeto também oferece envio automático de convites por e-mail, autenticação em duas etapas, gestão de despesas e leitura de notas fiscais com IA.


https://github.com/user-attachments/assets/eee210b4-e88d-4450-8a05-94353451df2e


## Funcionalidades

### Autenticação e segurança

- Cadastro, login e logout de usuários.
- Recuperação de senha pelas páginas nativas do Django.
- Autenticação em duas etapas (MFA) por código de seis dígitos enviado por e-mail.
- Código MFA armazenado como hash, com validade de 10 minutos.
- Limite de cinco tentativas para cada desafio MFA.
- Proteção das páginas internas para usuários autenticados.
- Painel administrativo do Django em `/admin/`.
  
<div align="center">

<img width="523" height="544" alt="image" src="https://github.com/user-attachments/assets/815a267c-480a-4a34-afb3-e170bc017b52" />


<p><i>Tela de autenticação em duas etapas (MFA)</i></p>

</div>

### Participantes

- Cadastro, edição, visualização e exclusão de perfis.
- Dados de nome, CPF, e-mail, cargo e telefone.
- Validação de CPF via cálculo no sistema.
- E-mail e CPF únicos por participante.
- Pesquisa avançada por nome, CPF, e-mail, cargo e telefone.
- Importação em massa por arquivos CSV e XLSX.
- Criação e atualização automática dos registros durante a importação.
- Geração de QR Code individual, vinculado à página do participante.
- Download do crachá individual em PDF.
- Geração de PDF com os QR Codes de todos os participantes ou de uma pesquisa filtrada.

<div align="center">

<img 
  width="523" 
  height="544" 
  alt="Tela de verificação MFA" 
  src="https://github.com/user-attachments/assets/02d6eb4b-dab6-44f9-917b-192610b93046"
/>

<p><i>Tela de Participantes e suas funcionalidades</i></p>

</div>


### Eventos

- Cadastro, listagem, detalhamento, edição e exclusão de eventos.
- Pesquisa por nome, data, horários e localização.
- Endereço completo com CEP, logradouro, número, complemento, bairro, cidade e UF.
- Consulta automática de endereço pela API ViaCEP durante o cadastro.
- Validação para impedir datas anteriores ao dia atual.
- Validação dos horários de início e término.
- Feedback visual de processamento durante a criação e o envio dos convites.

  <div align="center">

<img 
  width="523" 
  height="544" 
  alt="Tela de verificação MFA" 
  src="https://github.com/user-attachments/assets/8bba14ab-f6e8-4c95-a546-95194437f2c0"
/>

<p><i>Tela de Participantes e suas funcionalidades</i></p>

</div>


### Convites por e-mail

Ao criar um evento, um `post_save` agenda o envio dos convites após a confirmação da transação no banco de dados. Para cada participante com e-mail válido, o sistema:

1. Envia o QR Code pessoal.
2. Monta um e-mail com os dados do evento, como data, hora e endereço.
3. Inclui o link do perfil e o link para o Google Agenda.
<img width="443" height="717" alt="image" src="https://github.com/user-attachments/assets/9748ec79-8018-4b33-a722-faf67d5c029f" />


O modelo `EventEmailDelivery` mantém uma restrição única para cada combinação de evento e perfil. Essa proteção impede que uma nova execução do signal envie repetidamente o mesmo evento para a mesma pessoa. Se o SMTP falhar, a transação daquele destinatário é revertida e o envio poderá ser tentado novamente.

> Atualmente os e-mails são processados de forma síncrona. Com muitos participantes, a página permanece no feedback de envio até o SMTP concluir todos os destinatários.

### Presenças por QR Code

- Leitor de QR Code associado a cada evento.
- Identificação do participante pela URL armazenada no QR Code.
- Registro de uma única presença por participante em cada evento.
- Aviso quando uma presença já foi registrada.
- Listagem das presenças com data e hora.
- Exportação da lista de presença em CSV.

### Dispêndios

- Cadastro de vários dispêndios vinculados a um evento.
- Campos para descrição, fornecedor, valor, observação e comprovante.
- Upload de imagens e arquivos PDF.
- Totalização das despesas no detalhe do evento.
- Carregamento dos dispêndios já cadastrados por evento.

### Análise de nota fiscal com IA

- Envio de imagens JPG, PNG, WEBP e GIF ou documentos PDF.
- Limite de 10 MB por arquivo.
- Extração estruturada de fornecedor, itens, valores e observações.
- Preenchimento dos itens de despesa a partir do resultado da análise.
- Integração com a API Responses da OpenAI.
<img width="1468" height="774" alt="image" src="https://github.com/user-attachments/assets/a8a8b893-c849-4411-91d6-f48860285fc7" />

_Nota fiscal fictícia_

<img width="571" height="398" alt="image" src="https://github.com/user-attachments/assets/86657373-70cb-46b8-877a-2b78e6d8b355" />

_Após leitura da IA_

<img width="1513" height="885" alt="image" src="https://github.com/user-attachments/assets/2d74c38a-15e5-480d-b7fc-b0fc9be74a75" />




## Tecnologias

- Python e Django 6.
- SQLite.
- HTML, CSS e JavaScript.
- Pandas e OpenPyXL para importação de planilhas.
- QRCode e Pillow para geração dos códigos.
- ReportLab e FPDF para documentos PDF.
- `django-phonenumber-field` e `phonenumbers` para telefones.
- API Responses da OpenAI para leitura de notas fiscais.
- SMTP do Gmail para mensagens, convites e MFA.

## Estrutura do projeto

```text
Confirma_eventos/
├── accounts/                 # Cadastro, login, MFA e recuperação de senha
├── app/                      # Configurações, URLs e templates compartilhados
├── eventos/                  # Eventos, presenças, despesas e e-mails
│   ├── services/             # Serviço de criação e envio dos convites
│   ├── templates/            # Telas e template HTML do convite
│   └── migrations/           # Estrutura do banco de dados
├── management_profile/       # Participantes, importação, QR Codes e PDFs
├── media/                    # Arquivos enviados pelos usuários
├── static/                   # Imagens e arquivos estáticos
├── manage.py
└── requirements.txt
```

## Instalação local

### 1. Criar e ativar o ambiente virtual

No Windows/PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

No Linux ou macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

### 3. Configurar o ambiente

Crie um arquivo `.env` na raiz do projeto com as variáveis obrigatórias do Django e do e-mail:

```dotenv
SECRET_KEY=sua_chave_secreta
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app
```

Para habilitar a análise de notas fiscais, adicione:

```dotenv
OPENAI_API_KEY=sua_chave_da_api
OPENAI_INVOICE_MODEL=gpt-4o-mini
```

`OPENAI_API_KEY` é opcional para as demais funcionalidades. Sem ela, apenas a análise de notas fiscais ficará indisponível.

Os convites, MFA e recuperação de senha usam `EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD` do `.env`. Os demais dados de envio ficam no arquivo `app/settings.py`:

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `DEFAULT_FROM_EMAIL`

Em contas Gmail, utilize uma senha de app em vez da senha normal da conta. Não versionar chaves, senhas SMTP, `.env` ou outras credenciais.

Configure também `SITE_URL` com o endereço público da aplicação. Ele é usado para formar a URL gravada nos QR Codes enviados por e-mail:

```python
SITE_URL = "http://127.0.0.1:8000"
```

### 4. Preparar o banco de dados

```bash
python manage.py migrate
```

A migration `eventos.0009_eventemaildelivery` é necessária para o controle de envios únicos por evento e participante.

### 5. Criar um administrador (opcional)

```bash
python manage.py createsuperuser
```

### 6. Executar a aplicação

```bash
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`.

## Importação de participantes

O arquivo CSV ou XLSX deve conter as seguintes colunas:

| Coluna | Conteúdo |
| --- | --- |
| `name` | Nome do participante |
| `email` | E-mail único |
| `cpf` | CPF válido |
| `role` | Cargo ou função |
| `phone` | Telefone com DDD |

Linhas vazias são ignoradas. O resultado informa quantos perfis foram criados, atualizados e quais linhas apresentaram erro.

## Rotas principais

| Rota | Finalidade |
| --- | --- |
| `/` | Página inicial de eventos |
| `/login/` | Login e verificação MFA |
| `/register/` | Cadastro de usuário |
| `/list_profile/` | Lista de participantes |
| `/new_profile/` | Cadastro de participante |
| `/import_profiles/` | Importação CSV/XLSX |
| `/profiles/pdf/` | PDF com QR Codes |
| `/list_event/` | Lista de eventos |
| `/new_event/` | Cadastro e envio de novo evento |
| `/detail_event/<id>/` | Detalhes e despesas do evento |
| `/evento/<id>/scanner/` | Leitor de presença por QR Code |
| `/evento/<id>/presencas/` | Lista de presenças |
| `/evento/<id>/presencas/csv/` | Exportação das presenças |
| `/dispendios/<id>/` | Gestão de despesas do evento |
| `/admin/` | Administração do Django |

## Fluxo principal

```text
Cadastrar/importar participantes
            ↓
Gerar QR Codes individuais
            ↓
Criar evento
            ↓
Enviar um convite por participante
            ↓
Participante apresenta o QR Code
            ↓
Scanner registra a presença no evento
            ↓
Consultar ou exportar a lista de presença
```

## Verificações úteis

Validar a configuração do Django:

```bash
python manage.py check
```

Verificar migrations pendentes:

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
```

Executar os testes:

```bash
python manage.py test
```

## Observações para produção

Antes de publicar a aplicação:

- Defina `DEBUG = False`.
- Configure `ALLOWED_HOSTS`.
- Gere uma nova `SECRET_KEY` e mantenha as credenciais SMTP em variáveis de ambiente.
- Use HTTPS e configure cookies seguros.

## Licença

Este repositório é livre.
