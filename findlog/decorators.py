# findlog/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import redirect
from .models import Perfil


def superuser_required(view_func=None, redirect_field_name="next", login_url="login"):
    """
    Decorador que verifica se o usuário autenticado é superusuário.
    Caso não seja, redireciona para login_url.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def servidor_required(view_func):
    """
    Permite acesso apenas a usuários autenticados do tipo SERVIDOR (3).
    Administradores (1) e superusuários também têm permissão garantida.
    Redireciona para o login se não autenticado e dispara 403 se o perfil for incompatível.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Se não estiver logado, encaminha para a tela de login
        if not request.user.is_authenticated:
            return redirect("login")

        usuario = request.user

        # 2. Verifica se o perfil está ativo
        if not getattr(usuario, "ativo", True) or not usuario.is_active:
            raise PermissionDenied("Sua conta de usuário está inativa.")

        # 3. Permite Servidores (3), Administradores (1) ou Superusuários
        is_servidor = usuario.tipo == Perfil.TipoUsuario.SERVIDOR
        is_admin = usuario.tipo == Perfil.TipoUsuario.ADMINISTRADOR or usuario.is_superuser

        if not (is_servidor or is_admin):
            raise PermissionDenied("Acesso restrito ao perfil de servidor.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view