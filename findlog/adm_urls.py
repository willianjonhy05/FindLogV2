from django.urls import path
from .adm_views import (
    dashboard_adm,
    nova_instituicao,
    lista_instituicoes,
    excluir_instituicao,
    editar_instituicao,
    detalhes_instituicao,
    lista_categorias,
    nova_categoria,
    atualizar_categoria,
    excluir_categoria,
    view_categoria,
    lista_contatos,
    apagar_contato,
    view_contato,
    novo_usuario,
    lista_usuarios,
    visualizar_usuario,
    alternar_status_usuario,
    ativar_usuario,
    desativar_usuario,
    excluir_usuario,
    lista_salas,
    nova_sala,
    detalhes_sala,
    alternar_status_sala,
    editar_sala,
    excluir_sala,
    atualizar_item,
    detalhes_item,
    apagar_item,
    lista_itens,
    lista_reivindicacoes,
    detalhes_reivindicacao,
    atualizar_reivindicacao,
    apagar_reivindicacao,
    meu_perfil,
    trocar_minha_senha,
    editar_meu_perfil
)


urlpatterns = [
    path('', dashboard_adm, name='dashboard_admin'),
    path('instituicoes', lista_instituicoes, name='lista_instituicoes'),
    path('instituicoes/nova/', nova_instituicao, name='nova_instituicao'),
    path("instituicoes/<str:cnpj>/", detalhes_instituicao, name="detalhes_instituicao"),
    path("instituicoes/<str:cnpj>/editar/", editar_instituicao, name="editar_instituicao"),
    path("instituicoes/<str:cnpj>/excluir/", excluir_instituicao, name="excluir_instituicao"),

    path("categorias/", lista_categorias, name="lista_categorias"),
    path("categorias/nova/", nova_categoria, name="nova_categoria"),
    path("categorias/<str:codigo>/", view_categoria, name="view_categoria"),
    path("categorias/<str:codigo>/editar/", atualizar_categoria, name="atualizar_categoria"),
    path("categorias/<str:codigo>/excluir/", excluir_categoria, name="excluir_categoria"),

    path("contatos/", lista_contatos, name="lista_contatos"),
    path("contatos/<str:uuid>/", view_contato, name="view_contato"),
    path("contatos/<str:uuid>/excluir/", apagar_contato, name="apagar_contato"),


    path("usuarios/", lista_usuarios, name="lista_usuarios"),
    path("usuarios/novo/", novo_usuario, name="novo_usuario"),
    path("usuarios/<int:pk>/", visualizar_usuario, name="visualizar_usuario"),
    path("usuarios/<int:pk>/alternar-status/", alternar_status_usuario, name="alternar_status_usuario"),
    path("usuarios/<int:pk>/ativar/", ativar_usuario, name="ativar_usuario"),
    path("usuarios/<int:pk>/desativar/", desativar_usuario, name="desativar_usuario"),
    path("usuarios/<int:pk>/excluir/", excluir_usuario, name="excluir_usuario"),

    path("salas/", lista_salas, name="lista_salas"),
    path("salas/nova/", nova_sala, name="nova_sala"),
    path("salas/<str:codigo>/", detalhes_sala, name="detalhes_sala"),
    path("salas/<str:codigo>/editar/", editar_sala, name="editar_sala"),
    path("salas/<str:codigo>/alternar-status/", alternar_status_sala, name="alternar_status_sala"),
    path("salas/<str:codigo>/excluir/", excluir_sala, name="excluir_sala"),

    path("itens/", lista_itens, name="lista_itens"),
    path("itens/<str:codigo>/", detalhes_item, name="detalhes_item"),
    path("itens/<str:codigo>/editar/", atualizar_item, name="atualizar_item"),
    path("itens/<str:codigo>/excluir/", apagar_item, name="apagar_item"),

    path("reivindicacoes/", lista_reivindicacoes, name="lista_reivindicacoes"),
    path("reivindicacoes/<int:protocolo>/", detalhes_reivindicacao, name="detalhes_reivindicacao"),
    path("reivindicacoes/<int:protocolo>/editar/", atualizar_reivindicacao, name="atualizar_reivindicacao"),
    path("reivindicacoes/<int:protocolo>/excluir/", apagar_reivindicacao, name="apagar_reivindicacao"),    


    path("meu-perfil/", meu_perfil, name="meu_perfil"),
    path("meu-perfil/editar/", editar_meu_perfil, name="editar_meu_perfil"),
    path("meu-perfil/trocar-senha/", trocar_minha_senha, name="trocar_minha_senha"),    

]