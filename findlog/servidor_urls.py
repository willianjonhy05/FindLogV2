from django.urls import path
from .servidor_views import (
    servidor_painel,
    servidor_listar_itens,
    servidor_itens_por_categoria,
    servidor_cadastrar_sala,
    servidor_itens_por_sala,
    servidor_listar_salas,
    servidor_editar_sala,
    servidor_ativar_sala,
    servidor_desativar_sala,
    servidor_detalhar_sala,
    servidor_cadastrar_usuario
)

urlpatterns = [
    path("", servidor_painel, name="servidor_painel"),
    path("salas/", servidor_listar_salas, name="servidor_listar_salas"),
    path("salas/cadastrar/", servidor_cadastrar_sala, name="servidor_cadastrar_sala"),
    path("salas/<str:codigo>/", servidor_detalhar_sala, name="servidor_detalhar_sala"),
    path('salas/<str:codigo>/editar/', servidor_editar_sala, name='servidor_editar_sala'),
    path('salas/<str:codigo>/ativar/', servidor_ativar_sala, name='servidor_ativar_sala'),
    path('salas/<str:codigo>/desativar/', servidor_desativar_sala, name='servidor_desativar_sala'),    
    path("salas/<str:sala_codigo>/itens/", servidor_itens_por_sala, name="servidor_itens_por_sala"),

    path("usuarios/novo/", servidor_cadastrar_usuario, name="servidor_cadastrar_usuario"),

    path("itens/", servidor_listar_itens, name="servidor_listar_itens"),

    path("categorias/<int:categoria_id>/itens/", servidor_itens_por_categoria, name="servidor_itens_por_categoria"),

]