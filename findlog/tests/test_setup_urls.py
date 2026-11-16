from django.test import SimpleTestCase
from django.urls import reverse, resolve
from setup.views import (
    index,
    login_view,
    logout_view,
    selecionar_instituicao,
    esqueci_senha_view,
)
from findlog.views.adm_views import novo_usuario_instituicao, novo_servidor_instituicao


class UrlsMappingTestCase(SimpleTestCase):

    def test_url_home_resolves(self):
        """Testa se a URL raiz ('') resolve para a view index com o name 'home'."""
        url = reverse("home")
        self.assertEqual(url, "/")
        self.assertEqual(resolve(url).func, index)

    def test_url_login_resolves(self):
        """Testa se a URL '/login/' resolve para a view login_view."""
        url = reverse("login")
        self.assertEqual(url, "/login/")
        self.assertEqual(resolve(url).func, login_view)

    def test_url_logout_resolves(self):
        """Testa se a URL '/logout/' resolve para a view logout_view."""
        url = reverse("logout")
        self.assertEqual(url, "/logout/")
        self.assertEqual(resolve(url).func, logout_view)

    def test_url_selecionar_instituicao_resolves(self):
        """Testa se a URL '/selecionar-instituicao/' resolve corretamente."""
        url = reverse("selecionar_instituicao")
        self.assertEqual(url, "/selecionar-instituicao/")
        self.assertEqual(resolve(url).func, selecionar_instituicao)

    def test_url_recuperar_senha_resolves(self):
        """Testa se a URL '/esqueci-senha/' resolve utilizando o name 'recuperar_senha'."""
        url = reverse("recuperar_senha")
        self.assertEqual(url, "/esqueci-senha/")
        self.assertEqual(resolve(url).func, esqueci_senha_view)

    def test_url_novo_usuario_instituicao_resolves(self):
        """Testa se a URL com parâmetro token para novo usuário de instituição resolve corretamente."""
        url = reverse("novo_usuario_instituicao", args=["token-abc-123"])
        self.assertEqual(url, "/convite/token-abc-123/novo-usuario/")
        self.assertEqual(resolve(url).func, novo_usuario_instituicao)

    def test_url_novo_servidor_instituicao_resolves(self):
        """Testa se a URL com parâmetro token para novo servidor resolve corretamente."""
        url = reverse("novo_servidor_instituicao", args=["token-xyz-789"])
        self.assertEqual(url, "/convite/token-xyz-789/novo-servidor/")
        self.assertEqual(resolve(url).func, novo_servidor_instituicao)