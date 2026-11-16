from django.test import TestCase
from findlog.models import Reivindicacao, Item, Categoria, Sala, Instituicao, Perfil
from findlog.forms.reivindicacao import ReivindicacaoUpdateForm, ServidorAnaliseReivindicacaoForm  # Ajuste o import conforme a estrutura do seu projeto


class ReivindicacaoFormsTestCase(TestCase):

    def setUp(self):
        # Configuração de dados necessários para testar as reivindicações e formulários
        self.instituicao = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina Central",
            endereco="Centro",
            email="teresina@ifpi.edu.br",
            ativo=True
        )
        self.outra_instituicao = Instituicao.objects.create(
            cnpj="98765432000110",
            nome="IFPI Campus Parnaíba",
            endereco="Beira Mar",
            email="parnaiba@ifpi.edu.br",
            ativo=True
        )

        self.categoria = Categoria.objects.create(nome="Eletrônicos", ativa=True)
        
        self.sala_valida = Sala.objects.create(
            instituicao=self.instituicao,
            predio="Bloco A",
            andar="1º",
            nome="Sala de Apoio",
            ativa=True
        )
        self.sala_outra = Sala.objects.create(
            instituicao=self.outra_instituicao,
            predio="Bloco B",
            andar="2º",
            nome="Sala Parnaíba",
            ativa=True
        )

        self.autor = Perfil.objects.create(
            username="aluno_solicitante",
            email="aluno@exemplo.com",
            cpf="11122233344",
            nome="Aluno Solicitante"
        )
        self.responsavel = Perfil.objects.create(
            username="servidor_analista",
            email="servidor@ifpi.edu.br",
            cpf="55566677788",
            nome="Servidor Analista",
            tipo=Perfil.TipoUsuario.SERVIDOR
        )

        self.item = Item.objects.create(
            instituicao=self.instituicao,
            categoria=self.categoria,
            nome="Mochila Preta",
            status=Item.StatusItem.ENCONTRADO
        )

        self.reivindicacao = Reivindicacao.objects.create(
            autor=self.autor,
            item=self.item,
            instituicao=self.instituicao,
            pedido="Esta mochila é minha, contém cadernos."
        )

    # ==========================================
    # Testes para o ReivindicacaoUpdateForm
    # ==========================================
    def test_reivindicacao_update_form_valido(self):
        """Testa a atualização geral de uma reivindicação."""
        form_data = {
            "status": Reivindicacao.StatusReivindicacao.EM_ANALISE,
            "resposta_admin": "Estamos analisando os dados informados.",
            "responsavel_admin": self.responsavel.pk,
            "local_devolucao": self.sala_valida.pk,
        }
        form = ReivindicacaoUpdateForm(data=form_data, instance=self.reivindicacao)
        
        self.assertTrue(form.is_valid())
        reiv_atualizada = form.save()
        self.assertEqual(reiv_atualizada.status, Reivindicacao.StatusReivindicacao.EM_ANALISE)
        self.assertEqual(reiv_atualizada.responsavel_admin, self.responsavel)

    # ==========================================
    # Testes para o ServidorAnaliseReivindicacaoForm
    # ==========================================
    def test_servidor_analise_aprovada_com_local_valido(self):
        """Testa se a aprovação da reivindicação passa na validação quando o local de devolução é informado."""
        form_data = {
            "status": Reivindicacao.StatusReivindicacao.APROVADA,
            "local_devolucao": self.sala_valida.pk,
            "resposta_admin": "Reivindicação aprovada. Pode retirar.",
        }
        form = ServidorAnaliseReivindicacaoForm(data=form_data, instance=self.reivindicacao, instituicao=self.instituicao)
        
        self.assertTrue(form.is_valid())

    def test_servidor_analise_aprovada_sem_local_falha(self):
        """Testa se a aprovação é rejeitada caso o local de devolução não seja preenchido."""
        form_data = {
            "status": Reivindicacao.StatusReivindicacao.APROVADA,
            "local_devolucao": "",  # Vazio
            "resposta_admin": "Aprovado mas sem sala.",
        }
        form = ServidorAnaliseReivindicacaoForm(data=form_data, instance=self.reivindicacao, instituicao=self.instituicao)
        
        self.assertFalse(form.is_valid())
        self.assertIn("local_devolucao", form.errors)
        self.assertEqual(
            form.errors["local_devolucao"][0],
            "Informe a sala onde o usuário deverá comparecer para retirar o item."
        )

    def test_servidor_analise_rejeitada_com_justificativa(self):
        """Testa se a rejeição passa quando a justificativa (resposta_admin) é informada."""
        form_data = {
            "status": Reivindicacao.StatusReivindicacao.REJEITADA,
            "resposta_admin": "As evidências apresentadas são insuficientes.",
        }
        form = ServidorAnaliseReivindicacaoForm(data=form_data, instance=self.reivindicacao, instituicao=self.instituicao)
        
        self.assertTrue(form.is_valid())

    def test_servidor_analise_rejeitada_sem_justificativa_falha(self):
        """Testa se a rejeição é bloqueada caso o motivo (resposta_admin) esteja em branco."""
        form_data = {
            "status": Reivindicacao.StatusReivindicacao.REJEITADA,
            "resposta_admin": "",  # Vazio
        }
        form = ServidorAnaliseReivindicacaoForm(data=form_data, instance=self.reivindicacao, instituicao=self.instituicao)
        
        self.assertFalse(form.is_valid())
        self.assertIn("resposta_admin", form.errors)
        self.assertEqual(
            form.errors["resposta_admin"][0],
            "É obrigatório informar o motivo da rejeição para o solicitante."
        )

    def test_servidor_analise_filtra_salas_por_instituicao(self):
        """Testa se o queryset de local_devolucao restringe as salas apenas à instituição ativa."""
        form = ServidorAnaliseReivindicacaoForm(instituicao=self.instituicao)
        
        salas_disponiveis = form.fields["local_devolucao"].queryset
        self.assertIn(self.sala_valida, salas_disponiveis)
        self.assertNotIn(self.sala_outra, salas_disponiveis)

    def test_servidor_analise_sem_instituicao_zera_salas(self):
        """Testa se o formulário zera as opções de salas caso nenhuma instituição seja passada."""
        form = ServidorAnaliseReivindicacaoForm(instituicao=None)
        self.assertEqual(form.fields["local_devolucao"].queryset.count(), 0)