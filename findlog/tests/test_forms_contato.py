from django.test import TestCase
from findlog.forms.contato import ContatoForm  # Ajuste o import conforme a estrutura do seu projeto
from findlog.models import Contato


class ContatoFormTestCase(TestCase):

    def test_contato_form_valido(self):
        """Testa o formulário de contato preenchido com todos os campos obrigatórios válidos."""
        form_data = {
            "nome": "Maria Silva",
            "email": "maria@exemplo.com",
            "telefone": "86999998888",
            "assunto": Contato.Assuntos.DUVIDA,
            "mensagem": "Gostaria de tirar uma dúvida sobre o sistema de achados e perdidos."
        }
        form = ContatoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        contato = form.save()
        
        self.assertEqual(contato.nome, "Maria Silva")
        self.assertEqual(contato.email, "maria@exemplo.com")
        self.assertEqual(contato.assunto, Contato.Assuntos.DUVIDA)
        self.assertEqual(contato.mensagem, "Gostaria de tirar uma dúvida sobre o sistema de achados e perdidos.")

    def test_contato_form_campos_obrigatorios(self):
        """Testa se todos os campos configurados como required no __init__ geram erros se ausentes."""
        form = ContatoForm(data={})
        
        self.assertFalse(form.is_valid())
        
        # Garante que todos os 5 campos obrigatórios apresentem erro de validação
        campos_obrigatorios = ["nome", "email", "telefone", "assunto", "mensagem"]
        for campo in campos_obrigatorios:
            self.assertIn(campo, form.errors)

    def test_contato_form_email_invalido(self):
        """Testa se o formulário rejeita um formato de e-mail inválido."""
        form_data = {
            "nome": "João",
            "email": "email-sem-formato-valido",
            "telefone": "86988887777",
            "assunto": Contato.Assuntos.SUGESTAO,
            "mensagem": "Sugestão de melhoria no layout."
        }
        form = ContatoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)