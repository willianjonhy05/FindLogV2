from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from findlog.models import Perfil, Instituicao, VinculoInstituicao
from findlog.utils import (
    _obter_perfil_servidor,
    _obter_instituicao_servidor,
    redirecionar_origem,
)


class ServidorHelpersUtilsTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.inst_principal = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina Central",
            endereco="Centro",
            email="teresina@ifpi.edu.br",
            ativo=True,
        )
        self.inst_secundaria = Instituicao.objects.create(
            cnpj="29154694000101",
            nome="IFPI Campus Teresina Zona Sul",
            endereco="Zona Sul",
            email="zonasul@ifpi.edu.br",
            ativo=True,
        )
        self.inst_inativa = Instituicao.objects.create(
            cnpj="11222333000181",
            nome="IFPI Unidade Desativada",
            endereco="Rural",
            email="inativa@ifpi.edu.br",
            ativo=False,
        )

        self.servidor = Perfil.objects.create_user(
            username="servidor_teste",
            email="servidor@ifpi.edu.br",
            password="senha123",
            cpf="52998224725",
            nome="Servidor Teste",
            tipo=Perfil.TipoUsuario.SERVIDOR,
            ativo=True,
        )
        self.usuario_comum = Perfil.objects.create_user(
            username="aluno_teste",
            email="aluno@ifpi.edu.br",
            password="senha123",
            cpf="62648712015",
            nome="Aluno Teste",
            tipo=Perfil.TipoUsuario.USUARIO,
            ativo=True,
        )

        # Vincula o servidor às instituições
        VinculoInstituicao.objects.create(perfil=self.servidor, instituicao=self.inst_principal)
        VinculoInstituicao.objects.create(perfil=self.servidor, instituicao=self.inst_secundaria)
        VinculoInstituicao.objects.create(perfil=self.servidor, instituicao=self.inst_inativa)

    def _adicionar_sessao(self, request):
        """Injeta suporte a request.session nas requisições simuladas pelo RequestFactory."""
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request

    # ==========================================
    # Testes para _obter_perfil_servidor
    # ==========================================
    def test_obter_perfil_servidor_retorna_perfil_quando_servidor(self):
        """Retorna o objeto Perfil quando o usuário autenticado é do tipo SERVIDOR."""
        request = self.factory.get("/")
        request.user = self.servidor

        resultado = _obter_perfil_servidor(request)
        self.assertEqual(resultado, self.servidor)

    def test_obter_perfil_servidor_retorna_none_para_usuario_comum(self):
        """Retorna None quando o usuário autenticado não possui papel de SERVIDOR."""
        request = self.factory.get("/")
        request.user = self.usuario_comum

        resultado = _obter_perfil_servidor(request)
        self.assertIsNone(resultado)

    def test_obter_perfil_servidor_retorna_none_para_anonimo(self):
        """Retorna None quando a requisição vem de um usuário não autenticado."""
        request = self.factory.get("/")
        request.user = AnonymousUser()

        resultado = _obter_perfil_servidor(request)
        self.assertIsNone(resultado)

    # ==========================================
    # Testes para _obter_instituicao_servidor
    # ==========================================
    def test_obter_instituicao_servidor_usa_cnpj_da_sessao(self):
        """Prioriza a instituição ativa correspondente ao CNPJ salvo na sessão."""
        request = self.factory.get("/")
        request.user = self.servidor
        self._adicionar_sessao(request)
        request.session["instituicao_cnpj"] = self.inst_secundaria.cnpj

        inst = _obter_instituicao_servidor(request)
        self.assertEqual(inst, self.inst_secundaria)

    def test_obter_instituicao_servidor_ignora_cnpj_inativo_ou_invalido_e_usa_fallback(self):
        """Se o CNPJ da sessão for de instituição inativa ou não vinculada, retorna a primeira ativa."""
        request = self.factory.get("/")
        request.user = self.servidor
        self._adicionar_sessao(request)
        request.session["instituicao_cnpj"] = self.inst_inativa.cnpj

        inst = _obter_instituicao_servidor(request)
        self.assertIsNotNone(inst)
        self.assertTrue(inst.ativo)
        self.assertNotEqual(inst, self.inst_inativa)

    def test_obter_instituicao_servidor_sem_sessao_retorna_primeira_ativa(self):
        """Sem chave na sessão, retorna a primeira instituição ativa vinculada ao servidor."""
        request = self.factory.get("/")
        request.user = self.servidor
        self._adicionar_sessao(request)

        inst = _obter_instituicao_servidor(request)
        self.assertIn(inst, [self.inst_principal, self.inst_secundaria])
        self.assertTrue(inst.ativo)

    # ==========================================
    # Testes para redirecionar_origem
    # ==========================================
    def test_redirecionar_origem_usa_post_next_mesmo_host(self):
        """Redireciona para o parâmetro POST['next'] quando pertence ao mesmo host."""
        request = self.factory.post("/acao/", data={"next": "/servidor/itens/"})
        response = redirecionar_origem(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/servidor/itens/")

    def test_redirecionar_origem_usa_http_referer_mesmo_host(self):
        """Redireciona para HTTP_REFERER quando POST['next'] não existe e o host é permitido."""
        request = self.factory.post("/acao/", HTTP_REFERER="http://testserver/servidor/perfil/")
        response = redirecionar_origem(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "http://testserver/servidor/perfil/")

    def test_redirecionar_origem_bloqueia_host_externo_e_usa_fallback(self):
        """Bloqueia tentativas de Open Redirect para domínios externos e redireciona para o fallback."""
        request = self.factory.post("/acao/", data={"next": "https://site-malicioso.com/phishing"})
        response = redirecionar_origem(request, fallback="servidor_listar_salas")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("servidor_listar_salas"))

    def test_redirecionar_origem_sem_origem_vai_para_fallback(self):
        """Sem POST['next'] e sem HTTP_REFERER, redireciona diretamente para o fallback."""
        request = self.factory.post("/acao/")
        response = redirecionar_origem(request, fallback="servidor_listar_salas")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("servidor_listar_salas"))