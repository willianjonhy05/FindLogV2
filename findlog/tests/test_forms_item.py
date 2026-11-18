from django.test import TestCase
from findlog.models import Item, Categoria, Sala, Instituicao
from findlog.forms.item import ItemUpdateForm, ServidorItemForm  # Ajuste o import conforme a estrutura do seu projeto


class ItemFormsTestCase(TestCase):

    def setUp(self):
        # Configuração de dados base para os formulários
        self.instituicao = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina Central",
            endereco="Centro",
            email="teresina@ifpi.edu.br",
            ativo=True
        )
        self.outra_instituicao = Instituicao.objects.create(
            cnpj="11222333000181",
            nome="IFPI Campus Parnaíba",
            endereco="Beira Mar",
            email="parnaiba@ifpi.edu.br",
            ativo=True
        )

        self.categoria_ativa = Categoria.objects.create(nome="Eletrônicos", ativa=True)
        self.categoria_inativa = Categoria.objects.create(nome="Antigo", ativa=False)

        self.sala_inst = Sala.objects.create(
            instituicao=self.instituicao,
            predio="Bloco A",
            andar="1º",
            nome="Sala 101",
            ativa=True
        )
        self.sala_outra = Sala.objects.create(
            instituicao=self.outra_instituicao,
            predio="Bloco B",
            andar="2º",
            nome="Sala 202",
            ativa=True
        )

        self.item_existente = Item.objects.create(
            instituicao=self.instituicao,
            categoria=self.categoria_ativa,
            nome="Chaveiro",
            status=Item.StatusItem.PERDIDO
        )

    # ==========================================
    # Testes para o ItemUpdateForm
    # ==========================================
    def test_item_update_form_valido(self):
        """Testa se a atualização de um item existente funciona corretamente."""
        form_data = {
            "nome": "Chaveiro com 3 chaves",
            "categoria": self.categoria_ativa.pk,
            "instituicao": self.instituicao.pk,
            "status": Item.StatusItem.ENCONTRADO,
            "cor": "Azul",
            "material": "Metal"
        }
        form = ItemUpdateForm(data=form_data, instance=self.item_existente)
        
        self.assertTrue(form.is_valid())
        item_atualizado = form.save()
        self.assertEqual(item_atualizado.nome, "Chaveiro com 3 chaves")
        self.assertEqual(item_atualizado.status, Item.StatusItem.ENCONTRADO)
        self.assertEqual(item_atualizado.cor, "Azul")

    # ==========================================
    # Testes para o ServidorItemForm
    # ==========================================
    def test_servidor_item_form_valido(self):
        """Testa o preenchimento válido do formulário de registro de item pelo servidor."""
        form_data = {
            "nome": "Garrafa térmica",
            "categoria": self.categoria_ativa.pk,
            "status": Item.StatusItem.ENCONTRADO,
            "local": self.sala_inst.pk,
            "local_guardado": self.sala_inst.pk,
            "cor": "Inox",
            "tamanho": "500ml",
            "material": "Aço"
        }
        form = ServidorItemForm(data=form_data, instituicao=self.instituicao)
        
        self.assertTrue(form.is_valid())

    def test_servidor_item_form_filtra_categorias_apenas_ativas(self):
        """Testa se o queryset de categoria no ServidorItemForm inclui apenas as ativas."""
        form = ServidorItemForm(instituicao=self.instituicao)
        
        categorias_no_campo = form.fields["categoria"].queryset
        self.assertIn(self.categoria_ativa, categorias_no_campo)
        self.assertNotIn(self.categoria_inativa, categorias_no_campo)

    def test_servidor_item_form_restringe_salas_por_instituicao(self):
        """Testa se as salas (local e local_guardado) são filtradas estritamente pela instituição informada."""
        form = ServidorItemForm(instituicao=self.instituicao)
        
        locais_disponiveis = form.fields["local"].queryset
        
        # Deve conter a sala da instituição correta e excluir a da outra instituição
        self.assertIn(self.sala_inst, locais_disponiveis)
        self.assertNotIn(self.sala_outra, locais_disponiveis)

    def test_servidor_item_form_sem_instituicao_retorna_vazio(self):
        """Testa se o formulário bloqueia/zera as opções de salas caso nenhuma instituição seja fornecida."""
        form = ServidorItemForm(instituicao=None)
        
        self.assertEqual(form.fields["local"].queryset.count(), 0)
        self.assertEqual(form.fields["local_guardado"].queryset.count(), 0)