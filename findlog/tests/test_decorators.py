from unittest.mock import MagicMock
from django.test import RequestFactory, TestCase
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

# Substitua 'seu_app' pelo nome real do seu app Django
from findlog.decorators import superuser_required, servidor_required, usuario_required
from findlog.models import Perfil


class DecoratorsTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        
        # View fictícia simples para validar a execução bem-sucedida dos decoradores
        def dummy_view(request):
            return HttpResponse("Acesso Permitido")
        
        self.dummy_view = dummy_view

    # ==========================================
    # Testes para o decorador superuser_required
    # ==========================================
    def test_superuser_required_nao_autenticado(self):
        decorated_view = superuser_required(self.dummy_view)
        request = self.factory.get("/")
        request.user = MagicMock(is_authenticated=False)
        
        response = decorated_view(request)
        # O user_passes_test redireciona para a página de login
        self.assertEqual(response.status_code, 302)

    def test_superuser_required_usuario_comum(self):
        decorated_view = superuser_required(self.dummy_view)
        request = self.factory.get("/")
        request.user = MagicMock(is_authenticated=True, is_superuser=False)
        
        response = decorated_view(request)
        self.assertEqual(response.status_code, 302)

    def test_superuser_required_com_sucesso(self):
        decorated_view = superuser_required(self.dummy_view)
        request = self.factory.get("/")
        request.user = MagicMock(is_authenticated=True, is_superuser=True)
        
        response = decorated_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Acesso Permitido")

    # ==========================================
    # Testes para o decorador servidor_required
    # ==========================================
    def test_servidor_required_nao_autenticado(self):
        decorated_view = servidor_required(self.dummy_view)
        request = self.factory.get("/")
        request.user = MagicMock(is_authenticated=False)
        
        response = decorated_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")

    def test_servidor_required_usuario_inativo(self):
        decorated_view = servidor_required(self.dummy_view)
        request = self.factory.get("/")
        usuario = MagicMock(is_authenticated=True, is_active=False, ativo=True)
        request.user = usuario
        
        with self.assertRaises(PermissionDenied) as ctx:
            decorated_view(request)
        self.assertIn("Sua conta de usuário está inativa.", str(ctx.exception))

    def test_servidor_required_com_perfil_servidor(self):
        decorated_view = servidor_required(self.dummy_view)
        request = self.factory.get("/")
        usuario = MagicMock(is_authenticated=True, is_active=True, ativo=True)
        usuario.tipo = Perfil.TipoUsuario.SERVIDOR
        request.user = usuario
        
        response = decorated_view(request)
        self.assertEqual(response.status_code, 200)

    def test_servidor_required_com_perfil_administrador(self):
        decorated_view = servidor_required(self.dummy_view)
        request = self.factory.get("/")
        usuario = MagicMock(is_authenticated=True, is_active=True, ativo=True)
        usuario.tipo = Perfil.TipoUsuario.ADMINISTRADOR
        usuario.is_superuser = False
        request.user = usuario
        
        response = decorated_view(request)
        self.assertEqual(response.status_code, 200)

    def test_servidor_required_com_perfil_comum_negado(self):
        decorated_view = servidor_required(self.dummy_view)
        request = self.factory.get("/")
        usuario = MagicMock(is_authenticated=True, is_active=True, ativo=True)
        usuario.tipo = Perfil.TipoUsuario.USUARIO
        usuario.is_superuser = False
        request.user = usuario
        
        with self.assertRaises(PermissionDenied) as ctx:
            decorated_view(request)
        self.assertIn("Acesso restrito ao perfil de servidor.", str(ctx.exception))

    # ==========================================
    # Testes para o decorador usuario_required
    # ==========================================
    def test_usuario_required_nao_autenticado(self):
        decorated_view = usuario_required(self.dummy_view)
        request = self.factory.get("/")
        request.user = MagicMock(is_authenticated=False)
        
        response = decorated_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")

    def test_usuario_required_com_perfil_usuario(self):
        decorated_view = usuario_required(self.dummy_view)
        request = self.factory.get("/")
        usuario = MagicMock(is_authenticated=True, is_active=True, ativo=True)
        usuario.tipo = Perfil.TipoUsuario.USUARIO
        request.user = usuario
        
        response = decorated_view(request)
        self.assertEqual(response.status_code, 200)

    def test_usuario_required_com_perfil_servidor_negado(self):
        decorated_view = usuario_required(self.dummy_view)
        request = self.factory.get("/")
        usuario = MagicMock(is_authenticated=True, is_active=True, ativo=True)
        usuario.tipo = Perfil.TipoUsuario.SERVIDOR
        request.user = usuario
        
        with self.assertRaises(PermissionDenied) as ctx:
            decorated_view(request)
        self.assertIn("Acesso restrito ao perfil de usuário.", str(ctx.exception))