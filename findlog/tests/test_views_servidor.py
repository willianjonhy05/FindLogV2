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


class ServidorViewsIntegrationTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # 1. Instituições (CNPJs matematicamente válidos)
        self.inst_principal = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina Central",
            endereco="Centro",
            email="teresina@ifpi.edu.br",
            ativo=True,
        )
        self.inst_outra = Instituicao.objects.create(
            cnpj="11222333000181",
            nome="IFPI Campus Parnaíba",
            endereco="Beira Mar",
            email="parnaiba@ifpi.edu.br",
            ativo=True,
        )

        # 2. Salas
        self.sala_1 = Sala.objects.create(
            instituicao=self.inst_principal,
            predio="Bloco A",
            andar="1º",
            nome="Sala 101",
            ativa=True,
        )
        self.sala_guarda = Sala.objects.create(
            instituicao=self.inst_principal,
            predio="Bloco B",
            andar="Térreo",
            nome="Protocolo Achados",
            ativa=True,
        )
        self.sala_outra_inst = Sala.objects.create(
            instituicao=self.inst_outra,
            predio="Bloco C",
            andar="1º",
            nome="Sala Parnaíba",
            ativa=True,
        )

        # 3. Servidor logado (instituição principal)
        self.servidor = Perfil.objects.create_user(
            username="servidor_principal",
            email="servidor.principal@ifpi.edu.br",
            password="senhaServidor123",
            cpf="52998224725",
            nome="Servidor Principal",
            tipo=Perfil.TipoUsuario.SERVIDOR,
            sala=self.sala_guarda,
            ativo=True,
        )
        VinculoInstituicao.objects.create(
            perfil=self.servidor,
            instituicao=self.inst_principal,
        )

        # Outro servidor da mesma unidade (para testar filtro meus_itens vs unidade)
        self.colega_servidor = Perfil.objects.create_user(
            username="colega_servidor",
            email="colega@ifpi.edu.br",
            password="senha123",
            cpf="62648712015",
            nome="Colega Servidor",
            tipo=Perfil.TipoUsuario.SERVIDOR,
            sala=self.sala_1,
            ativo=True,
        )
        VinculoInstituicao.objects.create(
            perfil=self.colega_servidor,
            instituicao=self.inst_principal,
        )

        # Usuário comum (aluno/solicitante)
        self.usuario_comum = Perfil.objects.create_user(
            username="aluno_solicitante",
            email="aluno@ifpi.edu.br",
            password="senha123",
            cpf="11144477735",
            nome="Aluno Solicitante",
            tipo=Perfil.TipoUsuario.USUARIO,
            ativo=True,
        )
        VinculoInstituicao.objects.create(
            perfil=self.usuario_comum,
            instituicao=self.inst_principal,
        )

        # Login e definição da instituição ativa na sessão
        self.client.force_login(self.servidor)
        session = self.client.session
        session["instituicao_cnpj"] = self.inst_principal.cnpj
        session.save()

        # 4. Categorias e Itens
        self.categoria = Categoria.objects.create(
            nome="Eletrônicos",
            codigo="ELET",
            ativa=True,
        )

        self.item_meu = Item.objects.create(
            instituicao=self.inst_principal,
            categoria=self.categoria,
            local=self.sala_1,
            local_guardado=self.sala_guarda,
            nome="Calculadora Científica",
            status=Item.StatusItem.ENCONTRADO,
            usuario_registro=self.servidor,
        )

        self.item_colega = Item.objects.create(
            instituicao=self.inst_principal,
            categoria=self.categoria,
            local=self.sala_1,
            nome="Fone Bluetooth",
            status=Item.StatusItem.ENCONTRADO,
            usuario_registro=self.colega_servidor,
        )

        self.item_outra_inst = Item.objects.create(
            instituicao=self.inst_outra,
            categoria=self.categoria,
            local=self.sala_outra_inst,
            nome="Notebook Outra Unidade",
            status=Item.StatusItem.ENCONTRADO,
        )

        # 5. Reivindicações
        self.reiv_meu_item = Reivindicacao.objects.create(
            autor=self.usuario_comum,
            item=self.item_meu,
            instituicao=self.inst_principal,
            pedido="Calculadora Casio preta com etiqueta no verso.",
        )

        self.reiv_colega_item = Reivindicacao.objects.create(
            autor=self.usuario_comum,
            item=self.item_colega,
            instituicao=self.inst_principal,
            pedido="Fone JBL branco.",
        )

    # ==========================================
    # 1. PAINEL DO SERVIDOR E CONTROLE DE ACESSO
    # ==========================================
    def test_servidor_painel_carrega_metricas_e_qrcodes(self):
        response = self.client.get(reverse("servidor_painel"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "serv/index.html")
        self.assertEqual(response.context["instituicao"], self.inst_principal)
        self.assertEqual(response.context["qtde_itens"], 2)
        self.assertEqual(response.context["qtde_salas"], 2)
        self.assertIn("qrcode_usuario", response.context)
        self.assertIn("qrcode_servidor", response.context)

    def test_usuario_comum_nao_acessa_painel_servidor(self):
        # Usuário autenticado sem perfil de servidor recebe 403 Forbidden
        self.client.force_login(self.usuario_comum)
        response = self.client.get(reverse("servidor_painel"))
        self.assertEqual(response.status_code, 403)

        # Usuário anônimo (deslogado) é redirecionado para login (302)
        self.client.logout()
        response_anonimo = self.client.get(reverse("servidor_painel"))
        self.assertEqual(response_anonimo.status_code, 302)

    # ==========================================
    # 2. SALAS (LISTAGEM, CRUD, STATUS E ISOLAMENTO)
    # ==========================================
    def test_servidor_listar_salas_e_busca(self):
        response = self.client.get(reverse("servidor_listar_salas"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "serv/salas.html")
        salas_listadas = list(response.context["page_obj"])
        self.assertIn(self.sala_1, salas_listadas)
        self.assertNotIn(self.sala_outra_inst, salas_listadas)

        # Filtro de busca textual
        resp_busca = self.client.get(reverse("servidor_listar_salas"), {"q": "Protocolo"})
        self.assertEqual(list(resp_busca.context["page_obj"]), [self.sala_guarda])

    def test_servidor_cadastrar_sala_post(self):
        url = reverse("servidor_cadastrar_sala")
        self.assertEqual(self.client.get(url).status_code, 200)

        response = self.client.post(
            url,
            data={
                "nome": "Laboratório de Redes",
                "predio": "Bloco D",
                "andar": "2º",
                "telefone": "(86) 3215-9900",
                "descricao": "Sala ao lado da coordenação.",
            },
        )
        self.assertRedirects(response, reverse("servidor_listar_salas"))
        nova_sala = Sala.objects.get(nome="Laboratório de Redes")
        self.assertEqual(nova_sala.instituicao, self.inst_principal)
        self.assertTrue(nova_sala.ativa)

    def test_servidor_editar_sala(self):
        url = reverse("servidor_editar_sala", args=[self.sala_1.codigo])
        response = self.client.post(
            url,
            data={
                "nome": "Sala 101 Reformada",
                "predio": "Bloco A",
                "andar": "1º",
                "ativa": True,
            },
        )
        self.assertRedirects(response, reverse("servidor_listar_salas"))
        self.sala_1.refresh_from_db()
        self.assertEqual(self.sala_1.nome, "Sala 101 Reformada")

    def test_servidor_ativar_desativar_e_excluir_sala(self):
        # Desativar
        resp_desativar = self.client.post(
            reverse("servidor_desativar_sala", args=[self.sala_1.codigo])
        )
        self.assertEqual(resp_desativar.status_code, 302)
        self.sala_1.refresh_from_db()
        self.assertFalse(self.sala_1.ativa)

        # Reativar
        resp_ativar = self.client.post(
            reverse("servidor_ativar_sala", args=[self.sala_1.codigo])
        )
        self.assertEqual(resp_ativar.status_code, 302)
        self.sala_1.refresh_from_db()
        self.assertTrue(self.sala_1.ativa)

        # Excluir sala sem itens vinculados
        sala_temp = Sala.objects.create(
            instituicao=self.inst_principal,
            predio="Anexo",
            andar="Térreo",
            nome="Sala Temporária",
        )
        resp_excluir = self.client.post(
            reverse("servidor_excluir_sala", args=[sala_temp.codigo])
        )
        self.assertRedirects(resp_excluir, reverse("servidor_listar_salas"))
        self.assertFalse(Sala.objects.filter(pk=sala_temp.pk).exists())

    def test_isolamento_multi_tenant_sala_outra_instituicao_retorna_404(self):
        response = self.client.get(
            reverse("servidor_detalhar_sala", args=[self.sala_outra_inst.codigo])
        )
        self.assertEqual(response.status_code, 404)

    # ==========================================
    # 3. ITENS (CADASTRO, LISTAGEM, FILTROS E EXCLUSÃO)
    # ==========================================
    def test_servidor_listar_itens_e_filtros(self):
        url = reverse("servidor_listar_itens")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        itens = list(resp.context["page_obj"])
        self.assertEqual(len(itens), 2)
        self.assertNotIn(self.item_outra_inst, itens)

        # Filtro ?meus_itens=1
        resp_meus = self.client.get(url, {"meus_itens": "1"})
        self.assertEqual(list(resp_meus.context["page_obj"]), [self.item_meu])

    def test_servidor_itens_por_sala_e_por_categoria(self):
        resp_sala = self.client.get(
            reverse("servidor_itens_por_sala", args=[self.sala_guarda.codigo])
        )
        self.assertEqual(resp_sala.status_code, 200)
        self.assertEqual(list(resp_sala.context["page_obj"]), [self.item_meu])

        resp_cat = self.client.get(
            reverse("servidor_itens_por_categoria", args=[self.categoria.pk])
        )
        self.assertEqual(resp_cat.status_code, 200)
        self.assertEqual(resp_cat.context["total_itens"], 2)

    def test_servidor_cadastra_item_e_atualiza_item(self):
        url_cad = reverse("servidor_cadastra_item")
        resp_get = self.client.get(url_cad)
        self.assertEqual(resp_get.status_code, 200)

        resp_post = self.client.post(
            url_cad,
            data={
                "nome": "Guarda-chuva Preto",
                "categoria": self.categoria.nome,  # Datalist textual
                "status": Item.StatusItem.ENCONTRADO,
                "local": f"{self.sala_1.nome} - {self.sala_1.predio}",
                "local_guardado": self.sala_guarda.nome,
                "cor": "Preto",
            },
        )
        self.assertRedirects(resp_post, reverse("servidor_listar_itens"))
        novo_item = Item.objects.get(nome="Guarda-chuva Preto")
        self.assertEqual(novo_item.instituicao, self.inst_principal)
        self.assertEqual(novo_item.usuario_registro, self.servidor)
        self.assertEqual(novo_item.local, self.sala_1)

        # Atualização do item recém-criado
        url_edit = reverse("servidor_atualizar_item", args=[novo_item.uuid])
        resp_edit = self.client.post(
            url_edit,
            data={
                "categoria": self.categoria.nome,
                "nome": "Guarda-chuva Preto Automático",
                "cor": "Preto",
                "local": self.sala_1.nome,
                "local_guardado": self.sala_guarda.nome,
            },
        )
        self.assertRedirects(
            resp_edit, reverse("servidor_detalhes_item", args=[novo_item.uuid])
        )
        novo_item.refresh_from_db()
        self.assertEqual(novo_item.nome, "Guarda-chuva Preto Automático")

    def test_servidor_apagar_item_e_trava_item_devolvido(self):
        # Apagar item encontrado funciona
        resp_del = self.client.post(
            reverse("servidor_apagar_item", args=[self.item_colega.uuid])
        )
        self.assertRedirects(resp_del, reverse("servidor_listar_itens"))
        self.assertFalse(Item.objects.filter(pk=self.item_colega.pk).exists())

        # Item já devolvido é protegido contra exclusão
        self.item_meu.status = Item.StatusItem.DEVOLVIDO
        self.item_meu.save(update_fields=["status"])

        resp_block = self.client.post(
            reverse("servidor_apagar_item", args=[self.item_meu.uuid])
        )
        self.assertRedirects(
            resp_block, reverse("servidor_detalhes_item", args=[self.item_meu.uuid])
        )
        self.assertTrue(Item.objects.filter(pk=self.item_meu.pk).exists())

    # ==========================================
    # 4. USUÁRIOS & EQUIPE DA INSTITUIÇÃO
    # ==========================================
    def test_servidor_cadastrar_usuario_e_listar_equipe(self):
        url_cad = reverse("servidor_cadastrar_usuario")
        resp = self.client.post(
            url_cad,
            data={
                "nome": "Novo Colega Setor",
                "username": "novo.colega",
                "cpf": "03854892004",
                "email": "novocolega@ifpi.edu.br",
                "telefone": "(86) 99988-7766",
                "tipo": Perfil.TipoUsuario.SERVIDOR,
                "sala": f"{self.sala_1.nome} - {self.sala_1.predio}",
                "senha": "senhaProvisoria123",
                "confirmar_senha": "senhaProvisoria123",
            },
        )
        self.assertRedirects(resp, reverse("servidor_usuarios_instituicao"))
        criado = Perfil.objects.get(username="novo.colega")
        self.assertEqual(criado.sala, self.sala_1)
        self.assertTrue(
            VinculoInstituicao.objects.filter(
                perfil=criado, instituicao=self.inst_principal
            ).exists()
        )

    def test_servidor_ativar_desativar_e_visualizar_usuario(self):
        # Visualizar perfil do usuário
        resp_view = self.client.get(
            reverse("servidor_visualizar_usuario", args=[self.usuario_comum.username])
        )
        self.assertEqual(resp_view.status_code, 200)

        # Desativar usuário
        self.client.post(
            reverse("servidor_desativar_usuario", args=[self.usuario_comum.username])
        )
        self.usuario_comum.refresh_from_db()
        self.assertFalse(self.usuario_comum.ativo)

        # Reativar usuário
        self.client.post(
            reverse("servidor_ativar_usuario", args=[self.usuario_comum.username])
        )
        self.usuario_comum.refresh_from_db()
        self.assertTrue(self.usuario_comum.ativo)

        # Bloqueia auto-desativação
        self.client.post(
            reverse("servidor_desativar_usuario", args=[self.servidor.username])
        )
        self.servidor.refresh_from_db()
        self.assertTrue(self.servidor.ativo)

    # ==========================================
    # 5. REIVINDICAÇÕES (FILTRO PADRÃO E CONCLUSÃO DE ENTREGA)
    # ==========================================
    def test_servidor_listar_reivindicacoes_padrao_meus_itens_vs_unidade(self):
        url = reverse("servidor_listar_reivindicacoes")

        # Padrão: mostra apenas reivindicações de itens cadastrados pelo servidor logado
        resp_padrao = self.client.get(url)
        self.assertEqual(resp_padrao.status_code, 200)
        self.assertEqual(list(resp_padrao.context["page_obj"]), [self.reiv_meu_item])

        # Alternando switch (meus_itens=0): mostra todas da unidade
        resp_todas = self.client.get(url, {"meus_itens": "0"})
        self.assertEqual(resp_todas.context["total_reivindicacoes"], 2)

    def test_servidor_detalhar_e_concluir_reivindicacao_devolve_item(self):
        url = reverse(
            "servidor_detalhar_reivindicacao", args=[self.reiv_meu_item.protocolo]
        )
        self.assertEqual(self.client.get(url).status_code, 200)

        # Conclui a entrega do item ao solicitante
        response = self.client.post(
            url,
            data={
                "status": Reivindicacao.StatusReivindicacao.CONCLUIDA,
                "local_devolucao": f"{self.sala_guarda.nome} - {self.sala_guarda.predio}",
                "resposta_admin": "Identidade confirmada e objeto entregue ao aluno.",
            },
        )
        self.assertRedirects(response, url)

        self.reiv_meu_item.refresh_from_db()
        self.item_meu.refresh_from_db()

        self.assertEqual(
            self.reiv_meu_item.status, Reivindicacao.StatusReivindicacao.CONCLUIDA
        )
        self.assertEqual(self.reiv_meu_item.responsavel_admin, self.servidor)
        self.assertIsNotNone(self.reiv_meu_item.data_devolucao)

        # Verifica atualização automática no Item
        self.assertEqual(self.item_meu.status, Item.StatusItem.DEVOLVIDO)
        self.assertEqual(self.item_meu.dono, self.usuario_comum)

    # ==========================================
    # 6. MEU PERFIL E ALTERAÇÃO DE SENHA
    # ==========================================
    def test_servidor_visualizar_editar_perfil_e_alterar_senha(self):
        # Visualizar
        resp_view = self.client.get(reverse("servidor_visualizar_meu_perfil"))
        self.assertEqual(resp_view.status_code, 200)

        # Editar perfil
        resp_edit = self.client.post(
            reverse("servidor_editar_meu_perfil"),
            data={
                "nome": "Servidor Principal Atualizado",
                "telefone": "(86) 98877-6655",
                "sala": f"{self.sala_1.nome} - {self.sala_1.predio}",
            },
        )
        self.assertRedirects(resp_edit, reverse("servidor_visualizar_meu_perfil"))
        self.servidor.refresh_from_db()
        self.assertEqual(self.servidor.nome, "Servidor Principal Atualizado")
        self.assertEqual(self.servidor.sala, self.sala_1)

        # Alterar senha
        resp_senha = self.client.post(
            reverse("servidor_alterar_senha"),
            data={
                "old_password": "senhaServidor123",
                "new_password1": "novaSenhaServidor456",
                "new_password2": "novaSenhaServidor456",
            },
        )
        self.assertRedirects(resp_senha, reverse("servidor_visualizar_meu_perfil"))
        self.servidor.refresh_from_db()
        self.assertTrue(self.servidor.check_password("novaSenhaServidor456"))