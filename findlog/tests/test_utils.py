from django.test import TestCase, RequestFactory
from django.http import QueryDict
from django.core.paginator import Page
from django.contrib.messages import get_messages
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django import forms
from findlog.models import Perfil, Categoria
from findlog.utils import (
    higienizar_dados_post,
    verificar_acesso_admin,
    paginar_queryset,
    exibir_erros_formulario,
)


class UtilsFunctionsTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        
        # Usuários para os testes de verificação de admin
        self.admin_user = Perfil.objects.create_user(
            username="admin_test",
            email="admin@exemplo.com",
            password="senha123",
            cpf="52998224725",
            nome="Administrador",
            tipo=Perfil.TipoUsuario.ADMINISTRADOR
        )
        self.comum_user = Perfil.objects.create_user(
            username="comum_test",
            email="comum@exemplo.com",
            password="senha123",
            cpf="62648712015",
            nome="Usuário Comum",
            tipo=Perfil.TipoUsuario.USUARIO
        )

    def _adicionar_middlewares_request(self, request):
        """Helper para injetar session e messages na request simulada pelo RequestFactory."""
        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        request.session.save()
        
        message_middleware = MessageMiddleware(lambda req: None)
        message_middleware.process_request(request)
        return request

    # ==========================================
    # Testes para higienizar_dados_post
    # ==========================================
    def test_higienizar_dados_post_remove_mascaras(self):
        """Testa se a função remove pontuações e mantém apenas dígitos nos campos informados."""
        post_data = QueryDict("cpf=123.456.789-01&telefone=(86)99999-8888&cnpj=12.345.678/0001-95&nome=Teste", mutable=True)
        
        dados_limpos = higienizar_dados_post(post_data)
        
        self.assertEqual(dados_limpos["cpf"], "12345678901")
        self.assertEqual(dados_limpos["telefone"], "86999998888")
        self.assertEqual(dados_limpos["cnpj"], "12345678000195")
        self.assertEqual(dados_limpos["nome"], "Teste")

    def test_higienizar_dados_post_campos_vazios(self):
        """Testa se a higienização lida corretamente com campos vazios ou ausentes."""
        post_data = QueryDict("cpf=&nome=Sem Telefone", mutable=True)
        
        dados_limpos = higienizar_dados_post(post_data)
        
        self.assertEqual(dados_limpos["cpf"], "")
        self.assertEqual(dados_limpos["nome"], "Sem Telefone")

    # ==========================================
    # Testes para verificar_acesso_admin
    # ==========================================
    def test_verificar_acesso_admin_autoriza_admin(self):
        """Testa se administradores passam direto pela verificação (retorna None)."""
        request = self.factory.get("/")
        request.user = self.admin_user
        
        resultado = verificar_acesso_admin(request)
        self.assertIsNone(resultado)

    def test_verificar_acesso_admin_bloqueia_usuario_comum(self):
        """Testa se usuários comuns são redirecionados e recebem mensagem de erro."""
        request = self.factory.get("/")
        request.user = self.comum_user
        self._adicionar_middlewares_request(request)  # Adiciona suporte a mensagens
        
        response = verificar_acesso_admin(request, mensagem="Acesso restrito.", destino="home")
        
        self.assertEqual(response.status_code, 302)
        
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Acesso restrito.")

    # ==========================================
    # Testes para paginar_queryset
    # ==========================================
    def test_paginar_queryset_retorna_pagina_correta(self):
        """Testa se a paginação divide o queryset e retorna o objeto Page esperado."""
        for i in range(15):
            Categoria.objects.create(nome=f"Categoria {i}")
            
        # Ordenado por 'nome' em vez de 'id' para evitar erro de campo inexistente
        queryset = Categoria.objects.all().order_by("nome")
        
        request = self.factory.get("/?page=1")
        page_obj = paginar_queryset(request, queryset, por_pagina=10)
        
        self.assertIsInstance(page_obj, Page)
        self.assertEqual(len(page_obj.object_list), 10)
        self.assertTrue(page_obj.has_next())

        request_invalida = self.factory.get("/?page=abc")
        page_invalida = paginar_queryset(request_invalida, queryset, por_pagina=10)
        self.assertEqual(page_invalida.number, 1)

    # ==========================================
    # Testes para exibir_erros_formulario
    # ==========================================
    def test_exibir_erros_formulario_envia_mensagens(self):
        """Testa se os erros de um formulário inválido são convertidos em mensagens flash."""
        request = self.factory.post("/")
        self._adicionar_middlewares_request(request)  # Adiciona suporte a mensagens
        
        class DummyForm(forms.Form):
            nome = forms.CharField(required=True)

        form = DummyForm(data={})
        self.assertFalse(form.is_valid())
        
        exibir_erros_formulario(request, form)
        
        messages = list(get_messages(request))
        self.assertTrue(len(messages) > 0)
        self.assertIn("Nome: Este campo é obrigatório.", str(messages[0]))