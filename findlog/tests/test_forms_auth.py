from django.test import TestCase
from findlog.forms.auth import LoginForm, EsqueciSenhaForm
from findlog.models import Perfil


class AuthFormsTestCase(TestCase):

    def setUp(self):
        # Cria um usuário ativo para testes de login válido
        self.usuario_ativo = Perfil.objects.create_user(
            username="william",
            email="william@exemplo.com",
            password="senha123",
            nome="William",
            cpf="12345678901",
            ativo=True
        )
        
        # Cria um usuário inativo para testar o bloqueio no login
        self.usuario_inativo = Perfil.objects.create_user(
            username="inativo",
            email="inativo@exemplo.com",
            password="senha123",
            nome="Inativo",
            cpf="98765432100",
            ativo=False
        )

    # ==========================================
    # Testes para o LoginForm
    # ==========================================
    def test_login_form_valido(self):
        """Testa o LoginForm com credenciais corretas e usuário ativo."""
        form_data = {
            "email": "william@exemplo.com",
            "senha": "senha123"
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.user, self.usuario_ativo)

    def test_login_form_credenciais_invalidas(self):
        """Testa o LoginForm com senha incorreta ou e-mail inexistente."""
        form_data = {
            "email": "william@exemplo.com",
            "senha": "senhaerrada"
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("E-mail ou senha incorretos.", form.non_field_errors())

    def test_login_form_usuario_inativo(self):
        """Testa o LoginForm com usuário cuja conta está desativada."""
        form_data = {
            "email": "inativo@exemplo.com",
            "senha": "senha123"
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Esta conta de acesso está desativada.", form.non_field_errors())

    # ==========================================
    # Testes para o EsqueciSenhaForm
    # ==========================================
    def test_esqueci_senha_form_email(self):
        """Testa se o e-mail inserido é limpo de espaços e convertido para minúsculas."""
        form = EsqueciSenhaForm(data={"identificador": "  TESTE@Exemplo.COM  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["identificador"], "teste@exemplo.com")

    def test_esqueci_senha_form_cpf_com_mascara(self):
        """Testa se o CPF com pontuação/máscara é limpo, mantendo apenas os 11 dígitos."""
        form = EsqueciSenhaForm(data={"identificador": " 123.456.789-01 "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["identificador"], "12345678901")

    def test_esqueci_senha_form_cpf_sem_mascara(self):
        """Testa a limpeza correta de um CPF informado sem pontuação."""
        form = EsqueciSenhaForm(data={"identificador": "12345678901"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["identificador"], "12345678901")