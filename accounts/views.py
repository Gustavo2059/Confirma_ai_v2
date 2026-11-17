from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils import timezone
from django.contrib.auth.hashers import check_password

from .forms import CustomUserCreationForm
from .services.mfa import create_mfa_challenge
from .models import MFAChallenge


def register_view(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)

        if user_form.is_valid():
            user_form.save()

            # Redireciona para a página de login
            # após o registro bem-sucedido.
            return redirect('login')

    else:
        user_form = CustomUserCreationForm()

    return render(
        request,
        'register.html',
        {
            'user_form': user_form
        }
    )


def login_view(request):
    action = request.POST.get('action', 'login') if request.method == 'POST' else None

    # Só vincula o formulário ao POST quando for login normal
    login_form = AuthenticationForm(
        request=request,
        data=request.POST if action == 'login' else None
    )

    context = {
        'login_form': login_form,
        'show_mfa': False,
        'mfa_error': None,
    }

    def limpar_mfa():
        for key in ('mfa_user_id', 'mfa_challenge_id', 'mfa_backend'):
            request.session.pop(key, None)

    if request.method != 'POST':
        return render(request, 'login.html', context)

    # =========================================================
    # ETAPA 1 — E-MAIL + SENHA
    # =========================================================
    if action == 'login':
        email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        User = get_user_model()
        usuario = User.objects.filter(email__iexact=email).first()

        user = None

        if usuario:
            username_field = User.USERNAME_FIELD

            user = authenticate(
                request,
                **{
                    username_field: getattr(usuario, username_field),
                    'password': password,
                }
            )

        if user is None:
            login_form.add_error(None, 'E-mail ou senha inválidos.')
            return render(request, 'login.html', context)

        # Remove eventual MFA antigo
        limpar_mfa()

        try:
            challenge = create_mfa_challenge(user)
        except Exception:
            login_form.add_error(
                None,
                'Não foi possível enviar o código de verificação.'
            )
            return render(request, 'login.html', context)

        request.session.update({
            'mfa_user_id': user.pk,
            'mfa_challenge_id': challenge.pk,
            'mfa_backend': user.backend,
        })

        context['show_mfa'] = True

        return render(request, 'login.html', context)

    # =========================================================
    # ETAPA 2 — MFA
    # =========================================================
    if action == 'verify_mfa':
        context['show_mfa'] = True

        user_id = request.session.get('mfa_user_id')
        challenge_id = request.session.get('mfa_challenge_id')
        backend = request.session.get('mfa_backend')

        if not all((user_id, challenge_id, backend)):
            limpar_mfa()

            context['show_mfa'] = False
            login_form.add_error(
                None,
                'Sua verificação expirou. Faça login novamente.'
            )

            return render(request, 'login.html', context)

        User = get_user_model()

        try:
            user = User.objects.get(pk=user_id)

            challenge = MFAChallenge.objects.get(
                pk=challenge_id,
                user=user,
                used=False,
            )

        except (User.DoesNotExist, MFAChallenge.DoesNotExist):
            limpar_mfa()

            context['show_mfa'] = False
            login_form.add_error(
                None,
                'Código inválido ou expirado. Faça login novamente.'
            )

            return render(request, 'login.html', context)

        # Código expirado
        if challenge.expires_at <= timezone.now():
            challenge.used = True
            challenge.save(update_fields=['used'])

            context['mfa_error'] = 'O código expirou. Faça login novamente.'
            return render(request, 'login.html', context)

        # Limite de tentativas
        if challenge.attempts >= 5:
            challenge.used = True
            challenge.save(update_fields=['used'])

            context['mfa_error'] = 'Limite de tentativas atingido.'
            return render(request, 'login.html', context)

        code = request.POST.get('code', '').strip()

        # Formato inválido
        if not (code.isdigit() and len(code) == 6):
            context['mfa_error'] = 'Digite um código válido de 6 números.'
            return render(request, 'login.html', context)

        # Código incorreto
        if not check_password(code, challenge.code_hash):
            challenge.attempts += 1

            if challenge.attempts >= 5:
                challenge.used = True

            challenge.save(update_fields=['attempts', 'used'])

            restantes = max(0, 5 - challenge.attempts)

            context['mfa_error'] = (
                f'Código incorreto. Tentativas restantes: {restantes}.'
                if restantes
                else 'Limite de tentativas atingido.'
            )

            return render(request, 'login.html', context)

        # =====================================================
        # MFA CORRETO — LOGIN DEFINITIVO
        # =====================================================
        challenge.used = True
        challenge.save(update_fields=['used'])

        login(request, user, backend=backend)

        limpar_mfa()

        return redirect('list_profile')

    login_form.add_error(None, 'Solicitação inválida.')
    return render(request, 'login.html', context)


def logout_view(request):
    logout(request)

    return redirect('login')