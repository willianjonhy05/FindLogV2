from django.test import TestCase
from django.core.exceptions import ValidationError
from findlog.models import Reivindicacao, Item, Instituicao, Perfil, Categoria, Sala


class ReivindicacaoModelTestCase(TestCase):

    def setUp(self):
        # Configura as dependências necessárias
        self.instituicao_1 = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina",
            endereco="Centro",
            email="teresina@ifpi.edu.br"
        )
        self.instituicao_2 = Instituicao.objects.create(
            cnpj="32506317000190",
            nome="IFPI Campus Parnaíba",
            endereco="Beira Mar",
            email="parnaiba@ifpi.edu.br"
        )
        self.categoria = Categoria.objects.create(nome="Eletrônicos")
        self.sala = Sala.objects.create(predio="Bloco A", andar="1º", nome="Sala 101")
        self.autor = Perfil.objects.create(
            username="estudante",
            email="estudante@exemplo.com",
            cpf="12345678901",
            nome="Estudante Teste"
        )
        
        # Item disponível (ENCONTRADO) vinculado à instituição 1
        self.item_disponivel = Item.objects.create(
            instituicao=self.instituicao_1,
            categoria=self.categoria,
            nome="Smartphone",
            status=Item.StatusItem.ENCONTRADO
        )

        # Item já devolvido
        self.item_devolvido = Item.objects.create(
            instituicao=self.instituicao_1,
            categoria=self.categoria,
            nome="Relógio",
            status=Item.StatusItem.DEVOLVIDO
        )

        # Item com status perdido (não disponível para reivindicação)
        self.item_perdido = Item.objects.create(
            instituicao=self.instituicao_1,
            categoria=self.categoria,
            nome="Carteira",
            status=Item.StatusItem.PERDIDO
        )

    def test_criacao_reivindicacao_com_sucesso(self):
        """Testa se a reivindicação é criada com sucesso quando as regras são atendidas."""
        reivindicacao = Reivindicacao.objects.create(
            autor=self.autor,
            item=self.item_disponivel,
            instituicao=self.instituicao_1,
            pedido="Este smartphone é meu, possui uma capinha azul."
        )

        self.assertTrue(reivindicacao.protocolo)
        self.assertEqual(reivindicacao.status, Reivindicacao.StatusReivindicacao.PENDENTE)
        self.assertEqual(str(reivindicacao), f"Reivindicação #{reivindicacao.protocolo}")

    def test_validacao_item_devolvido(self):
        """Testa se lança ValidationError ao tentar reivindicar um item que já foi devolvido."""
        reivindicacao = Reivindicacao(
            autor=self.autor,
            item=self.item_devolvido,
            instituicao=self.instituicao_1,
            pedido="Quero reivindicar este relógio."
        )

        with self.assertRaises(ValidationError) as ctx:
            reivindicacao.full_clean()
        
        self.assertIn("item", ctx.exception.error_dict)
        self.assertIn("já foi devolvido", str(ctx.exception))

    def test_validacao_item_nao_encontrado(self):
        """Testa se lança ValidationError ao tentar reivindicar um item que não está com status ENCONTRADO."""
        reivindicacao = Reivindicacao(
            autor=self.autor,
            item=self.item_perdido,
            instituicao=self.instituicao_1,
            pedido="Minha carteira perdida."
        )

        with self.assertRaises(ValidationError) as ctx:
            reivindicacao.full_clean()
        
        self.assertIn("item", ctx.exception.error_dict)
        self.assertIn("não está disponível", str(ctx.exception))

    def test_validacao_instituicao_divergente(self):
        """Testa se lança ValidationError caso a instituição da reivindicação seja diferente da instituição do item."""
        reivindicacao = Reivindicacao(
            autor=self.autor,
            item=self.item_disponivel,
            instituicao=self.instituicao_2,  # Instituição diferente do item
            pedido="Reivindicando em outro campus."
        )

        with self.assertRaises(ValidationError) as ctx:
            reivindicacao.full_clean()

        self.assertIn("A reivindicação deve pertencer à mesma instituição do item.", str(ctx.exception))