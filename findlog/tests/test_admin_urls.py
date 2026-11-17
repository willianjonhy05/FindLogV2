from django.test import TestCase, Client
from django.urls import reverse
from findlog.models import Perfil, Instituicao, Categoria, Sala, Item, Contato, Reivindicacao


class AdminUrlsIntegrationTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # Configuração do Superusuário autenticado para as rotas administrativas
        self.superuser = Perfil.objects.create_superuser(
            username="super_admin",
            email="admin@ifpi.edu.br",
            password="senhaSuper123",
            cpf="52998224725",
            nome="Super Administrador",
            tipo=Perfil.TipoUsuario.ADMINISTRADOR
        )
        self.client.force_login(self.superuser)

        # Dados de suporte para os testes das rotas com parâmetros
        self.instituicao = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina Central",
            endereco="Centro",
            email="teresina@ifpi.edu.br",
            ativo=True
        )

        self.categoria = Categoria.objects.create(
            nome="Eletrônicos",
            codigo="ELET",
            ativa=True
        )

        self.sala = Sala.objects.create(
            instituicao=self.instituicao,
            predio="Bloco A",
            andar="1º",
            nome="Sala 101",
            ativa=True
        )

        self.item = Item.objects.create(
            instituicao=self.instituicao,
            categoria=self.categoria,
            nome="Notebook Dell",
            status=Item.StatusItem.ENCONTRADO,
            usuario_registro=self.superuser  # Adicione esta linha
        )

        self.contato = Contato.objects.create(
            nome="Visitante Teste",
            email="visitante@exemplo.com",
            assunto=Contato.Assuntos.DUVIDA,
            mensagem="Dúvida sobre objeto."
        )

        self.usuario_comum = Perfil.objects.create_user(
            username="usuario_comum",
            email="comum@exemplo.com",
            password="senha123",
            cpf="62648712015",
            nome="Usuário Comum",
            tipo=Perfil.TipoUsuario.USUARIO
        )

        self.reivindicacao = Reivindicacao.objects.create(
            autor=self.usuario_comum,
            item=self.item,
            instituicao=self.instituicao,
            pedido="Este notebook é meu."
        )

    # ==========================================
    # 1. DASHBOARD
    # ==========================================
    def test_url_dashboard_admin(self):
        response = self.client.get(reverse("dashboard_admin"))
        self.assertEqual(response.status_code, 200)

    # ==========================================
    # 2. INSTITUIÇÕES
    # ==========================================
    def test_urls_instituicoes(self):
        self.assertEqual(reverse("lista_instituicoes"), "/adm/instituicoes")
        self.assertEqual(reverse("nova_instituicao"), "/adm/instituicoes/nova/")
        self.assertEqual(reverse("detalhes_instituicao", args=[self.instituicao.cnpj]), f"/adm/instituicoes/{self.instituicao.cnpj}/")
        self.assertEqual(reverse("editar_instituicao", args=[self.instituicao.cnpj]), f"/adm/instituicoes/{self.instituicao.cnpj}/editar/")
        self.assertEqual(reverse("excluir_instituicao", args=[self.instituicao.cnpj]), f"/adm/instituicoes/{self.instituicao.cnpj}/excluir/")

        # Testando requisições GET nas páginas principais
        self.assertEqual(self.client.get(reverse("lista_instituicoes")).status_code, 200)
        self.assertEqual(self.client.get(reverse("nova_instituicao")).status_code, 200)
        self.assertEqual(self.client.get(reverse("detalhes_instituicao", args=[self.instituicao.cnpj])).status_code, 200)

    # ==========================================
    # 3. CATEGORIAS
    # ==========================================
    def test_urls_categorias(self):
        self.assertEqual(reverse("lista_categorias"), "/adm/categorias/")
        self.assertEqual(reverse("nova_categoria"), "/adm/categorias/nova/")
        self.assertEqual(reverse("view_categoria", args=[self.categoria.codigo]), f"/adm/categorias/{self.categoria.codigo}/")
        self.assertEqual(reverse("atualizar_categoria", args=[self.categoria.codigo]), f"/adm/categorias/{self.categoria.codigo}/editar/")
        self.assertEqual(reverse("excluir_categoria", args=[self.categoria.codigo]), f"/adm/categorias/{self.categoria.codigo}/excluir/")

        self.assertEqual(self.client.get(reverse("lista_categorias")).status_code, 200)
        self.assertEqual(self.client.get(reverse("nova_categoria")).status_code, 200)
        self.assertEqual(self.client.get(reverse("view_categoria", args=[self.categoria.codigo])).status_code, 200)

    # ==========================================
    # 4. CONTATOS
    # ==========================================
    def test_urls_contatos(self):
        self.assertEqual(reverse("lista_contatos"), "/adm/contatos/")
        self.assertEqual(reverse("view_contato", args=[self.contato.uuid]), f"/adm/contatos/{self.contato.uuid}/")
        self.assertEqual(reverse("apagar_contato", args=[self.contato.pk]), f"/adm/contatos/{self.contato.pk}/excluir/")

        self.assertEqual(self.client.get(reverse("lista_contatos")).status_code, 200)
        self.assertEqual(self.client.get(reverse("view_contato", args=[self.contato.uuid])).status_code, 200)

    # ==========================================
    # 5. USUÁRIOS
    # ==========================================
    def test_urls_usuarios(self):
        self.assertEqual(reverse("lista_usuarios"), "/adm/usuarios/")
        self.assertEqual(reverse("novo_usuario"), "/adm/usuarios/novo/")
        self.assertEqual(reverse("visualizar_usuario", args=[self.usuario_comum.pk]), f"/adm/usuarios/{self.usuario_comum.pk}/")
        self.assertEqual(reverse("alternar_status_usuario", args=[self.usuario_comum.pk]), f"/adm/usuarios/{self.usuario_comum.pk}/alternar-status/")
        self.assertEqual(reverse("ativar_usuario", args=[self.usuario_comum.pk]), f"/adm/usuarios/{self.usuario_comum.pk}/ativar/")
        self.assertEqual(reverse("desativar_usuario", args=[self.usuario_comum.pk]), f"/adm/usuarios/{self.usuario_comum.pk}/desativar/")
        self.assertEqual(reverse("excluir_usuario", args=[self.usuario_comum.pk]), f"/adm/usuarios/{self.usuario_comum.pk}/excluir/")

        self.assertEqual(self.client.get(reverse("lista_usuarios")).status_code, 200)
        self.assertEqual(self.client.get(reverse("novo_usuario")).status_code, 200)
        self.assertEqual(self.client.get(reverse("visualizar_usuario", args=[self.usuario_comum.pk])).status_code, 200)

    # ==========================================
    # 6. SALAS E AMBIENTES
    # ==========================================
    def test_urls_salas(self):
        self.assertEqual(reverse("lista_salas"), "/adm/salas/")
        self.assertEqual(reverse("nova_sala"), "/adm/salas/nova/")
        self.assertEqual(reverse("detalhes_sala", args=[self.sala.pk]), f"/adm/salas/{self.sala.pk}/")
        self.assertEqual(reverse("editar_sala", args=[self.sala.codigo]), f"/adm/salas/{self.sala.codigo}/editar/")
        self.assertEqual(reverse("alternar_status_sala", args=[self.sala.codigo]), f"/adm/salas/{self.sala.codigo}/alternar-status/")
        self.assertEqual(reverse("excluir_sala", args=[self.sala.codigo]), f"/adm/salas/{self.sala.codigo}/excluir/")

        self.assertEqual(self.client.get(reverse("lista_salas")).status_code, 200)
        self.assertEqual(self.client.get(reverse("nova_sala")).status_code, 200)
        self.assertEqual(self.client.get(reverse("detalhes_sala", args=[self.sala.pk])).status_code, 200)

    # ==========================================
    # 7. ITENS
    # ==========================================
    def test_urls_itens(self):
        self.assertEqual(reverse("lista_itens"), "/adm/itens/")
        self.assertEqual(reverse("detalhes_item", args=[self.item.uuid]), f"/adm/itens/{self.item.uuid}/")
        self.assertEqual(reverse("atualizar_item", args=[self.item.uuid]), f"/adm/itens/{self.item.uuid}/editar/")
        self.assertEqual(reverse("apagar_item", args=[self.item.uuid]), f"/adm/itens/{self.item.uuid}/excluir/")

        self.assertEqual(self.client.get(reverse("lista_itens")).status_code, 200)
        self.assertEqual(self.client.get(reverse("detalhes_item", args=[self.item.uuid])).status_code, 200)

    # ==========================================
    # 8. REIVINDICAÇÕES
    # ==========================================
    def test_urls_reivindicacoes(self):
        self.assertEqual(reverse("lista_reivindicacoes"), "/adm/reivindicacoes/")
        self.assertEqual(reverse("detalhes_reivindicacao", args=[self.reivindicacao.protocolo]), f"/adm/reivindicacoes/{self.reivindicacao.protocolo}/")
        self.assertEqual(reverse("atualizar_reivindicacao", args=[self.reivindicacao.protocolo]), f"/adm/reivindicacoes/{self.reivindicacao.protocolo}/editar/")
        self.assertEqual(reverse("apagar_reivindicacao", args=[self.reivindicacao.protocolo]), f"/adm/reivindicacoes/{self.reivindicacao.protocolo}/excluir/")

        self.assertEqual(self.client.get(reverse("lista_reivindicacoes")).status_code, 200)
        self.assertEqual(self.client.get(reverse("detalhes_reivindicacao", args=[self.reivindicacao.protocolo])).status_code, 200)

    # ==========================================
    # 9. PERFIL DO ADMINISTRADOR
    # ==========================================
    def test_urls_perfil_admin(self):
        self.assertEqual(reverse("meu_perfil"), "/adm/meu-perfil/")
        self.assertEqual(reverse("editar_meu_perfil"), "/adm/meu-perfil/editar/")
        self.assertEqual(reverse("trocar_minha_senha"), "/adm/meu-perfil/trocar-senha/")

        self.assertEqual(self.client.get(reverse("meu_perfil")).status_code, 200)
        self.assertEqual(self.client.get(reverse("editar_meu_perfil")).status_code, 200)
        self.assertEqual(self.client.get(reverse("trocar_minha_senha")).status_code, 200)