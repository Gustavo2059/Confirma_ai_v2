from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

#from django.utils.decorators import method_decorator
#from app.decorator import login_required_com_mensagem
#@method_decorator(login_required_com_mensagem, name='dispatch')

#me chame de neo, fiz meu próprio decorator, papo de cybersecurity nasa

def login_required_com_mensagem(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa fazer login para acessar esta página.')
            return redirect(f"{reverse('login')}?next={request.get_full_path()}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view