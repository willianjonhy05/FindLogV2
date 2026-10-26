from django.urls import path
from .servidor_views import servidor_painel

urlpatterns = [
    path("", servidor_painel, name="servidor_painel"),

]