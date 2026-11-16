from django.test import TestCase
from findlog.models import Item, Categoria, Instituicao, Perfil, Sala


class ItemModelTestCase(TestCase):

    def setUp(self):
        # Configura as dependências necessárias para criar um Item
        self.instituicao = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI",
            endereco="Centro",
            email="ifpi@edu.br"
        )
        self.categoria = Categoria.objects.create(nome="Eletrônicos")
        self.sala = Sala.objects.create(predio="Bloco A", andar="1º", nome="Sala 101")
        self.perfil = Perfil.objects.create(
            username="usuario_teste",
            email="teste@exemplo.com",
            cpf="12345678901",
            nome="Usuário Teste"
        )

    def test_criacao_item_gera_codigo_e_uuid(self):
        """Testa se ao criar um item, o código aleatório e o UUID são gerados automaticamente."""
        item = Item.objects.create(
            instituicao=self.instituicao,
            categoria=self.categoria,
            nome="Calculadora Científica",
            tamanho="Médio",
            cor="Preto",
            material="Plástico",
            marca_ou_modelo="Casio",
            usuario_registro=self.perfil,
            local=self.sala,
            status=Item.StatusItem.ENCONTRADO,
            descricao="Calculadora encontrada na sala 101."
        )

        # Verifica UUID e Código
        self.assertTrue(item.uuid)
        self.assertTrue(item.codigo)
        self.assertEqual(len(item.codigo), 8)
        self.assertEqual(item.status, Item.StatusItem.ENCONTRADO)
        self.assertEqual(item.nome, "Calculadora Científica")

    def test_propriedade_qr_code(self):
        """Testa se a property qr_code retorna uma string base64 válida em formato Data URI."""
        item = Item.objects.create(
            instituicao=self.instituicao,
            nome="Chaveiro"
        )

        qrcode_str = item.qr_code
        self.assertTrue(qrcode_str.startswith("data:image/png;base64,"))
        self.assertGreater(len(qrcode_str), 50)

    def test_str_representation(self):
        """Testa o método __str__ com nome e sem nome cadastrado."""
        item1 = Item.objects.create(
            instituicao=self.instituicao,
            nome="Mochila"
        )
        item2 = Item.objects.create(
            instituicao=self.instituicao,
            nome=None
        )

        self.assertEqual(str(item1), f"Mochila ({item1.codigo})")
        self.assertEqual(str(item2), f"Item {item2.codigo}")