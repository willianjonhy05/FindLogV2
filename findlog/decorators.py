# findlog/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


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