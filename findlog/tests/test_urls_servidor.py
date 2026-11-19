from django.test import TestCase, Client
from django.urls import reverse
from findlog.models import (
    Perfil,
    Instituicao,
    VinculoInstituicao,
    Categoria,
    Sala,
    Item,
    Reivindicacao,
)


class ServidorUrlsIntegrationTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # Instituição ativa (CNPJ matematicamente válido)
        self.instituicao = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina Central",
            endereco="Centro",
            email="teresina@ifpi.edu.br",
            ativo=True,
        )

        # Servidor autenticado e vinculado à instituição
        self.servidor = Perfil.objects.create_user(
            username="servidor_urls",
            email="servidor.urls@ifpi.edu.br",
            password="senhaServidor123",
            cpf="52998224725",
            nome="Servidor Teste URLs",
            tipo=Perfil.TipoUsuario.SERVIDOR,
            ativo=True,
        )
        VinculoInstituicao.objects.create(
            perfil=self.servidor,
            instituicao=self.instituicao,
        )

        # Faz login e define a instituição ativa na sessão do servidor
        self.client.force_login(self.servidor)
        session = self.client.session
        session["instituicao_cnpj"] = self.instituicao.cnpj
        session.save()

        # Usuário comum vinculado à mesma instituição
        self.usuario_comum = Perfil.objects.create_user(
            username="aluno_urls",
            email="aluno.urls@ifpi.edu.br",
            password="senha123",
            cpf="62648712015",
            nome="Aluno Teste URLs",
            tipo=Perfil.TipoUsuario.USUARIO,
            ativo=True,
        )
        VinculoInstituicao.objects.create(
            perfil=self.usuario_comum,
            instituicao=self.instituicao,
        )

        # Dados auxiliares (Categoria, Sala, Item, Reivindicação)
        self.categoria = Categoria.objects.create(
            nome="Acessórios",
            codigo="ACES",
            ativa=True,
        )

        self.sala = Sala.objects.create(
            instituicao=self.instituicao,
            predio="Bloco B",
            andar="2º",
            nome="Sala 202",
            ativa=True,
        )

        self.item = Item.objects.create(
            instituicao=self.instituicao,
            categoria=self.categoria,
            local=self.sala,
            nome="Garrafa Térmica",
            status=Item.StatusItem.ENCONTRADO,
            usuario_registro=self.servidor,
        )

        self.reivindicacao = Reivindicacao.objects.create(
            autor=self.usuario_comum,
            item=self.item,
            instituicao=self.instituicao,
            pedido="Garrafa azul deixada na sala 202.",
        )

    # ==========================================
    # 1. PAINEL DO SERVIDOR
    # ==========================================
    def test_url_servidor_painel(self):
        url = reverse("servidor_painel")
        self.assertTrue(url.endswith("/"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # ==========================================
    # 2. SALAS
    # ==========================================
    def test_urls_servidor_salas(self):
        # Valida resolução de todas as rotas de salas (usando self.sala.pk como identificador)
        url_listar = reverse("servidor_listar_salas")
        url_cadastrar = reverse("servidor_cadastrar_sala")
        url_detalhar = reverse("servidor_detalhar_sala", args=[self.sala.codigo])
        url_editar = reverse("servidor_editar_sala", args=[self.sala.codigo])
        url_excluir = reverse("servidor_excluir_sala", args=[self.sala.codigo])
        url_ativar = reverse("servidor_ativar_sala", args=[self.sala.codigo])
        url_desativar = reverse("servidor_desativar_sala", args=[self.sala.codigo])
        url_itens_sala = reverse("servidor_itens_por_sala", args=[self.sala.codigo])

        self.assertTrue(url_listar.endswith("/painel/salas/"))
        self.assertTrue(url_cadastrar.endswith("/painel/salas/cadastrar/"))
        self.assertTrue(url_detalhar.endswith(f"/painel/salas/{self.sala.codigo}/"))
        self.assertTrue(url_editar.endswith(f"/painel/salas/{self.sala.codigo}/editar/"))
        self.assertTrue(url_excluir.endswith(f"/painel/salas/{self.sala.codigo}/excluir/"))
        self.assertTrue(url_ativar.endswith(f"/painel/salas/{self.sala.codigo}/ativar/"))
        self.assertTrue(url_desativar.endswith(f"/painel/salas/{self.sala.codigo}/desativar/"))
        self.assertTrue(url_itens_sala.endswith(f"/painel/salas/{self.sala.codigo}/itens/"))

        # Testa respostas GET das páginas de visualização/formulário
        self.assertEqual(self.client.get(url_listar).status_code, 200)
        self.assertEqual(self.client.get(url_cadastrar).status_code, 200)
        self.assertEqual(self.client.get(url_detalhar).status_code, 200)
        self.assertEqual(self.client.get(url_editar).status_code, 200)
        self.assertEqual(self.client.get(url_itens_sala).status_code, 200)

    # ==========================================
    # 3. MEU PERFIL (SERVIDOR)
    # ==========================================
    def test_urls_servidor_meu_perfil(self):
        url_perfil = reverse("servidor_visualizar_meu_perfil")
        url_editar = reverse("servidor_editar_meu_perfil")
        url_senha = reverse("servidor_alterar_senha")

        self.assertTrue(url_perfil.endswith("/painel/meu-perfil/"))
        self.assertTrue(url_editar.endswith("/painel/meu-perfil/editar/"))
        self.assertTrue(url_senha.endswith("/painel/meu-perfil/alterar-senha/"))

        self.assertEqual(self.client.get(url_perfil).status_code, 200)
        self.assertEqual(self.client.get(url_editar).status_code, 200)
        self.assertEqual(self.client.get(url_senha).status_code, 200)

    # ==========================================
    # 4. USUÁRIOS DA INSTITUIÇÃO
    # ==========================================
    def test_urls_servidor_usuarios(self):
        url_listar = reverse("servidor_usuarios_instituicao")
        url_novo = reverse("servidor_cadastrar_usuario")
        url_visualizar = reverse("servidor_visualizar_usuario", args=[self.usuario_comum.username])
        url_ativar = reverse("servidor_ativar_usuario", args=[self.usuario_comum.username])
        url_desativar = reverse("servidor_desativar_usuario", args=[self.usuario_comum.username])

        self.assertTrue(url_listar.endswith("/painel/usuarios/"))
        self.assertTrue(url_novo.endswith("/painel/usuarios/novo/"))
        self.assertTrue(url_visualizar.endswith(f"/painel/usuarios/{self.usuario_comum.username}/"))
        self.assertTrue(url_ativar.endswith(f"/painel/usuarios/{self.usuario_comum.username}/ativar/"))
        self.assertTrue(url_desativar.endswith(f"/painel/usuarios/{self.usuario_comum.username}/desativar/"))

        self.assertEqual(self.client.get(url_listar).status_code, 200)
        self.assertEqual(self.client.get(url_novo).status_code, 200)
        self.assertEqual(self.client.get(url_visualizar).status_code, 200)

    # ==========================================
    # 5. ITENS
    # ==========================================
    def test_urls_servidor_itens(self):
        url_listar = reverse("servidor_listar_itens")
        url_novo = reverse("servidor_cadastra_item")
        url_detalhes = reverse("servidor_detalhes_item", args=[self.item.uuid])
        url_editar = reverse("servidor_atualizar_item", args=[self.item.uuid])
        url_apagar = reverse("servidor_apagar_item", args=[self.item.uuid])

        self.assertTrue(url_listar.endswith("/painel/itens/"))
        self.assertTrue(url_novo.endswith("/painel/itens/novo/"))
        self.assertTrue(url_detalhes.endswith(f"/painel/itens/{self.item.uuid}/"))
        self.assertTrue(url_editar.endswith(f"/painel/itens/{self.item.uuid}/editar/"))
        self.assertTrue(url_apagar.endswith(f"/painel/itens/{self.item.uuid}/apagar/"))

        self.assertEqual(self.client.get(url_listar).status_code, 200)
        self.assertEqual(self.client.get(url_novo).status_code, 200)
        self.assertEqual(self.client.get(url_detalhes).status_code, 200)
        self.assertEqual(self.client.get(url_editar).status_code, 200)

    # ==========================================
    # 6. REIVINDICAÇÕES
    # ==========================================
    def test_urls_servidor_reivindicacoes(self):
        # Nota: a rota no urlpatterns está grafada como "reividicacoes/" (sem o primeiro 'n')
        url_listar = reverse("servidor_listar_reivindicacoes")
        url_detalhar = reverse("servidor_detalhar_reivindicacao", args=[self.reivindicacao.protocolo])

        self.assertTrue(url_listar.endswith("/painel/reividicacoes/"))
        self.assertTrue(url_detalhar.endswith(f"/painel/reivindicacoes/{self.reivindicacao.protocolo}/"))

        self.assertEqual(self.client.get(url_listar).status_code, 200)
        self.assertEqual(self.client.get(url_detalhar).status_code, 200)

    # ==========================================
    # 7. ITENS POR CATEGORIA
    # ==========================================
    def test_url_servidor_itens_por_categoria(self):
        url_categoria = reverse("servidor_itens_por_categoria", args=[self.categoria.codigo])

        self.assertTrue(url_categoria.endswith(f"/painel/categorias/{self.categoria.codigo}/itens/"))
        self.assertEqual(self.client.get(url_categoria).status_code, 200)