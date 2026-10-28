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
    servidor_cadastrar_usuario,
    servidor_usuarios_instituicao,
    servidor_visualizar_usuario,
    servidor_desativar_usuario,
    servidor_ativar_usuario,
    servidor_cadastra_item,
    servidor_detalhes_item,
    servidor_atualizar_item
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


    path("usuarios/", servidor_usuarios_instituicao, name="servidor_usuarios_instituicao"),
    path("usuarios/novo/", servidor_cadastrar_usuario, name="servidor_cadastrar_usuario"),
    path("usuarios/<int:pk>/", servidor_visualizar_usuario, name="servidor_visualizar_usuario"),
    path("usuarios/<int:pk>/ativar/", servidor_ativar_usuario, name="servidor_ativar_usuario"),
    path("usuarios/<int:pk>/desativar/", servidor_desativar_usuario, name="servidor_desativar_usuario"),

    path("itens/", servidor_listar_itens, name="servidor_listar_itens"),
    path("itens/novo/", servidor_cadastra_item, name="servidor_cadastra_item"),
    path("itens/<str:codigo>/", servidor_detalhes_item, name="servidor_detalhes_item"),
    path("itens/<str:codigo>/editar/", servidor_atualizar_item, name="servidor_atualizar_item"),

    path("categorias/<int:categoria_id>/itens/", servidor_itens_por_categoria, name="servidor_itens_por_categoria"),

]