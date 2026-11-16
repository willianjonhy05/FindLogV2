from django.test import TestCase
from findlog.forms.categoria import CategoriaForm  # Ajuste o import conforme a estrutura do seu projeto
from findlog.models import Categoria


class CategoriaFormTestCase(TestCase):

    def setUp(self):
        # Cria uma categoria inicial para testar validações de duplicidade
        self.categoria_existente = Categoria.objects.create(
            nome="Eletrônicos",
            descricao="Dispositivos eletrônicos e computadores"
        )

    def test_categoria_form_valido(self):
        """Testa o preenchimento correto do formulário para criar uma nova categoria."""
        form_data = {
            "nome": "Material de Escritório",
            "descricao": "Canetas, papéis e grampeadores"
        }
        form = CategoriaForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        categoria = form.save()
        self.assertEqual(categoria.nome, "Material de Escritório")
        self.assertTrue(categoria.codigo)  # Verifica se o código do model foi gerado no save

    def test_categoria_form_nome_vazio_ou_branco(self):
        """Testa se o formulário rejeita nomes vazios ou compostos apenas por espaços."""
        form = CategoriaForm(data={
            "nome": "   ",
            "descricao": "Descrição sem nome"
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)
        self.assertEqual(form.errors["nome"][0], "O nome da categoria é obrigatório.")

    def test_categoria_form_nome_duplicado_case_insensitive(self):
        """Testa se o formulário bloqueia nomes duplicados independentemente de maiúsculas/minúsculas."""
        form = CategoriaForm(data={
            "nome": "eletrônicos",  # Já existe "Eletrônicos" cadastrada no setUp
            "descricao": "Tentativa de duplicata"
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)
        self.assertEqual(form.errors["nome"][0], "Já existe uma categoria cadastrada com este nome.")

    def test_categoria_form_edicao_proprio_nome(self):
        """Testa se ao editar uma categoria existente mantendo o próprio nome, a validação é bem-sucedida."""
        form = CategoriaForm(
            data={
                "nome": "Eletrônicos",
                "descricao": "Descrição atualizada"
            },
            instance=self.categoria_existente
        )
        
        self.assertTrue(form.is_valid())
        categoria_atualizada = form.save()
        self.assertEqual(categoria_atualizada.descricao, "Descrição atualizada")