from django.test import TestCase
from findlog.models import Categoria


class CategoriaModelTestCase(TestCase):

    def test_criacao_categoria_gera_codigo_e_slug(self):
        """Testa se ao criar uma categoria, o código e o slug são gerados automaticamente."""
        categoria = Categoria.objects.create(
            nome="Eletrônicos e Informática",
            descricao="Dispositivos eletrônicos e computadores"
        )
        
        # Verifica se o código foi gerado (tamanho padrão baseado no nome, ex: EL + 2 dígitos)
        self.assertTrue(categoria.codigo)
        self.assertLessEqual(len(categoria.codigo), 6)
        
        # Verifica se o slug foi gerado corretamente utilizando o slugify
        self.assertEqual(categoria.slug, "eletronicos-e-informatica")
        
        # Verifica o valor padrão do campo 'ativa'
        self.assertTrue(categoria.ativa)

    def test_geracao_slug_unico_para_nomes_duplicados(self):
        """Testa se categorias com o mesmo nome recebem slugs únicos (ex: -2)."""
        cat1 = Categoria.objects.create(nome="Material Escolar")
        cat2 = Categoria.objects.create(nome="Material Escolar")
        
        self.assertEqual(cat1.slug, "material-escolar")
        self.assertEqual(cat2.slug, "material-escolar-2")

    def test_str_representation(self):
        """Testa o método __str__ do model Categoria."""
        categoria = Categoria.objects.create(nome="Livros e Revistas")
        esperado = f"{categoria.codigo} - Livros e Revistas"
        self.assertEqual(str(categoria), esperado)

    def test_ordenacao_padrao(self):
        """Testa se as categorias são ordenadas por nome por padrão (Meta ordering)."""
        Categoria.objects.create(nome="Zebra")
        Categoria.objects.create(nome="Abacaxi")
        Categoria.objects.create(nome="Carro")

        categorias = list(Categoria.objects.all())
        self.assertEqual(categorias[0].nome, "Abacaxi")
        self.assertEqual(categorias[1].nome, "Carro")
        self.assertEqual(categorias[2].nome, "Zebra")