from django.test import TestCase
from findlog.models import Sala, Instituicao
from findlog.forms.sala import SalaForm, ServidorSalaForm, ServidorUpdateSalaForm  # Ajuste o import conforme a estrutura do seu projeto


class SalaFormsTestCase(TestCase):

    def setUp(self):
        # Criação de dados base para os testes de formulários de sala
        self.instituicao_ativa = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina Central",
            endereco="Centro",
            email="teresina@ifpi.edu.br",
            ativo=True
        )
        self.instituicao_inativa = Instituicao.objects.create(
            cnpj="87261970000129",
            nome="IFPI Campus Inativo",
            endereco="Fora de Operação",
            email="inativo@ifpi.edu.br",
            ativo=False
        )

        self.sala_existente = Sala.objects.create(
            instituicao=self.instituicao_ativa,
            predio="Bloco A",
            andar="1º",
            nome="Laboratório de Redes",
            telefone="(86) 3215-1111",
            sala_de_aula=False,
            laboratorio=True
        )

    # ==========================================
    # Testes para o SalaForm
    # ==========================================
    def test_sala_form_valido_e_sanitizacao_telefone(self):
        """Testa o cadastro válido via SalaForm e se o telefone é limpo (apenas dígitos)."""
        form_data = {
            "nome": "Sala 101",
            "predio": "Bloco B",
            "andar": "Térreo",
            "telefone": "(86) 3215-2222",
            "descricao": "Sala de aula padrão",
            "sala_de_aula": True,
            "laboratorio": False,
            "instituicao": self.instituicao_ativa.pk,
            "ativa": True,
        }
        form = SalaForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        sala = form.save()
        
        self.assertEqual(sala.telefone, "8632152222")
        self.assertEqual(sala.instituicao, self.instituicao_ativa)
        self.assertTrue(sala.sala_de_aula)

    def test_sala_form_filtra_instituicoes_apenas_ativas(self):
        """Testa se o queryset do campo instituicao exibe apenas instituições ativas."""
        form = SalaForm()
        queryset_instituicoes = form.fields["instituicao"].queryset
        
        self.assertIn(self.instituicao_ativa, queryset_instituicoes)
        self.assertNotIn(self.instituicao_inativa, queryset_instituicoes)

    # ==========================================
    # Testes para o ServidorSalaForm
    # ==========================================
    def test_servidor_sala_form_valido(self):
        """Testa o preenchimento válido do formulário de criação de sala pelo Servidor."""
        form_data = {
            "nome": "Auditório Central",
            "predio": "Central",
            "andar": "Térreo",
            "telefone": "(86) 99999-8888",
            "descricao": "Auditório principal para eventos.",
            "sala_de_aula": False,
            "laboratorio": False,
        }
        form = ServidorSalaForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        sala = form.save(commit=False)
        self.assertEqual(sala.telefone, "86999998888")

    def test_servidor_sala_form_campos_obrigatorios(self):
        """Testa se nome, prédio e andar são obrigatórios no ServidorSalaForm."""
        form = ServidorSalaForm(data={})
        
        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)
        self.assertIn("predio", form.errors)
        self.assertIn("andar", form.errors)

    # ==========================================
    # Testes para o ServidorUpdateSalaForm
    # ==========================================
    def test_servidor_update_sala_form_valido(self):
        """Testa a atualização bem-sucedida de uma sala existente pelo ServidorUpdateSalaForm."""
        form_data = {
            "nome": "Laboratório de Redes Atualizado",
            "predio": "Bloco A",
            "andar": "2º",
            "telefone": "(86) 3215-3333",
            "sala_de_aula": True,
            "laboratorio": True,
            "descricao": "Atualizado com novos computadores.",
        }
        form = ServidorUpdateSalaForm(data=form_data, instance=self.sala_existente)
        
        self.assertTrue(form.is_valid())
        sala_atualizada = form.save()
        
        self.assertEqual(sala_atualizada.nome, "Laboratório de Redes Atualizado")
        self.assertEqual(sala_atualizada.andar, "2º")
        self.assertTrue(sala_atualizada.sala_de_aula)