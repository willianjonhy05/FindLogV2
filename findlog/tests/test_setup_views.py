from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from unittest.mock import patch
from findlog.models import Perfil, Instituicao, Categoria, Item

# Substitua 'seu_app' pelo nome real do seu aplicativo Django se necessário
# from seu_app.views import index, login_view, selecionar_instituicao, logout_view, esqueci_senha_view


class ViewsTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        
        # Criação de dados base para os testes
        self.instituicao_1 = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina",
            endereco="Centro",
            email="teresina@ifpi.edu.br",
            ativo=True
        )
        self.instituicao_2 = Instituicao.objects.create(
            cnpj="98765432000110",
            nome="IFPI Campus Parnaíba",
            endereco="Beira Mar",
            email="parnaiba@ifpi.edu.br",
            ativo=True
        )

        self.usuario_comum = Perfil.objects.create_user(
            username="usuario_comum",
            email="usuario@exemplo.com",
            password="senha123",
            nome="Usuário Comum",
            cpf="12345678901",
            tipo=Perfil.TipoUsuario.USUARIO,
            ativo=True
        )
        self.usuario_comum.instituicao.add(self.instituicao_1)

        self.usuario_inativo = Perfil.objects.create_user(
            username="usuario_inativo",
            email="inativo@exemplo.com",
            password="senha123",
            nome="Usuário Inativo",
            cpf="98765432100",
            tipo=Perfil.TipoUsuario.USUARIO,
            ativo=False
        )

        self.admin_user = Perfil.objects.create_superuser(
            username="admin",
            email="admin@exemplo.com",
            password="senha123",
            cpf="11122233344",
            nome="Administrador"
        )

    # ==========================================
    # Testes para a view index (Contato)
    # ==========================================
    def test_index_get(self):
        """Testa o carregamento da página inicial (GET)."""
        response = self.client.get(reverse("home"))  # Ajuste o nome da URL se necessário ("index" ou "home")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "public/index.html")
        self.assertIn("form_contato", response.context)

    def test_index_post_valido(self):
        """Testa o envio bem-sucedido de uma mensagem de contato (POST)."""
        dados = {
            "nome": "Visitante",
            "email": "visitante@exemplo.com",
            "telefone": "86999998888",
            "assunto": "DUVIDA",  # Deve corresponder a uma das opções de Assuntos.choices
            "mensagem": "Gostaria de saber como funciona o sistema."
        }
        response = self.client.post(reverse("home"), dados)
        self.assertRedirects(response, reverse("home"))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Mensagem enviada com sucesso", str(messages[0]))
        

    def test_index_post_invalido(self):
        """Testa o envio de formulário de contato com dados inválidos."""
        dados = {
            "nome": "",
            "email": "email-invalido",
            "assunto": "",
            "mensagem": ""
        }
        response = self.client.post(reverse("home"), dados)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "public/index.html")
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Não foi possível enviar a mensagem" in str(m) for m in messages))

    # ==========================================
    # Testes para a view login_view
    # ==========================================
    def test_login_view_get_nao_autenticado(self):
        """Testa o carregamento da tela de login para usuários não autenticados."""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "public/login.html")

    def test_login_view_ja_autenticado(self):
        """Testa se usuário já logado é redirecionado corretamente."""
        self.client.force_login(self.usuario_comum)
        response = self.client.get(reverse("login"))
        # Como possui 1 instituição vinculada, o fluxo redireciona por perfil
        self.assertEqual(response.status_code, 302)

    def test_login_view_usuario_inativo_ja_logado(self):
        """Testa se usuário inativo já logado é deslogado e recebe tela 403."""
        self.client.force_login(self.usuario_inativo)
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")

    @patch("findlog.forms.auth.LoginForm.is_valid", return_value=True)
    def test_login_post_com_sucesso_uma_instituicao(self, mock_is_valid):
        """Testa o login bem-sucedido de um usuário com exatamente uma instituição vinculada."""
        form_mock = self.client.class_instance if hasattr(self.client, 'class_instance') else None
        
        # Simulando o atributo .user populado pelo form customizado de login
        with patch("setup.views.LoginForm") as MockLoginForm:
            instance = MockLoginForm.return_value
            instance.is_valid.return_value = True
            instance.user = self.usuario_comum

            response = self.client.post(reverse("login"), {"email": "usuario@exemplo.com", "password": "senha123"})
            
            # Verifica se fixou a única instituição na sessão e redirecionou
            self.assertEqual(self.client.session.get("instituicao_cnpj"), self.instituicao_1.cnpj)
            self.assertEqual(self.client.session.get("username"), self.usuario_comum.username)

    def test_login_post_credenciais_invalidas(self):
        """Testa tentativa de login com credenciais incorretas."""
        response = self.client.post(reverse("login"), {"email": "errado@exemplo.com", "password": "errada"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "public/login.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Falha na autenticação" in str(m) for m in messages))

    # ==========================================
    # Testes para a view selecionar_instituicao
    # ==========================================
    def test_selecionar_instituicao_requer_login(self):
        """Testa se usuários não autenticados são barrados na seleção de instituição."""
        response = self.client.get(reverse("selecionar_instituicao"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('selecionar_instituicao')}")

    def test_selecionar_instituicao_get_admin(self):
        """Testa o carregamento da seleção de instituição para administrador (vê todas)."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("selecionar_instituicao"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "public/selecionar_instituicao.html")
        self.assertEqual(len(response.context["instituicoes"]), 2)

    def test_selecionar_instituicao_post_escolha_valida(self):
        """Testa a escolha via POST de uma instituição válida pelo admin."""
        self.client.force_login(self.admin_user)
        response = self.client.post(reverse("selecionar_instituicao"), {"instituicao_cnpj": self.instituicao_2.cnpj})
        
        self.assertEqual(self.client.session.get("instituicao_cnpj"), self.instituicao_2.cnpj)
        self.assertEqual(self.client.session.get("instituicao_nome"), self.instituicao_2.nome)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Instituição ativa alterada" in str(m) for m in messages))

    # ==========================================
    # Testes para a view logout_view
    # ==========================================
    def test_logout_view(self):
        """Testa se o logout encerra a sessão e redireciona para o login."""
        self.client.force_login(self.usuario_comum)
        response = self.client.get(reverse("logout"))
        
        self.assertRedirects(response, reverse("login"))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Sua sessão foi encerrada" in str(m) for m in messages))

    # ==========================================
    # Testes para a view esqueci_senha_view
    # ==========================================
    def test_esqueci_senha_get(self):
        """Testa o carregamento da página de recuperação de senha."""
        response = self.client.get(reverse("recuperar_senha"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "public/esqueci_senha.html")

    def test_esqueci_senha_ja_autenticado(self):
        self.client.force_login(self.usuario_comum)
        response = self.client.get(reverse("recuperar_senha"))
        # Como já está autenticado, a view executa redirect("login")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

    @patch("setup.views.send_mail")
    def test_esqueci_senha_post_email_valido(self, mock_send_mail):
        """Testa o fluxo de solicitação de nova senha com um e-mail válido."""
        mock_send_mail.return_value = 1  # Simula envio bem-sucedido de 1 e-mail
        
        response = self.client.post(reverse("recuperar_senha"), {"identificador": "usuario@exemplo.com"})
        
        self.assertRedirects(response, reverse("login"))
        mock_send_mail.assert_called_once()
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("uma nova senha provisória foi enviada" in str(m) for m in messages))

    @patch("setup.views.send_mail", side_effect=Exception("Erro no servidor de email"))
    def test_esqueci_senha_post_falha_envio_email(self, mock_send_mail):
        """Testa o comportamento caso ocorra erro ao disparar o e-mail de senha provisória."""
        response = self.client.post(reverse("recuperar_senha"), {"identificador": "usuario@exemplo.com"})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "public/esqueci_senha.html")
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Houve um problema temporário ao enviar o e-mail" in str(m) for m in messages))