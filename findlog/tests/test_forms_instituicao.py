from django.test import TestCase
from findlog.models import Instituicao
from findlog.forms.instituicao import InstituicaoForm, InstituicaoUpdateForm  # Ajuste o import conforme a estrutura do seu projeto


class InstituicaoFormsTestCase(TestCase):

    def setUp(self):
        # Cria uma instituição inicial para testar duplicidade de CNPJ no form de criação
        self.instituicao_existente = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina Central",
            endereco="Rua Anísio de Abreu",
            telefone="8632156000",
            email="central@ifpi.edu.br",
            ativo=True
        )

    # ==========================================
    # Testes para o InstituicaoForm (Criação)
    # ==========================================
    def test_instituicao_form_valido(self):
        """Testa a criação de uma nova instituição com dados válidos e formatação limpa."""
        form_data = {
            "cnpj": "98765432000110",
            "nome": "IFPI Campus Parnaíba",
            "endereco": "Av. São Sebastião",
            "telefone": "(86) 3322-1122",
            "email": "parnaiba@ifpi.edu.br",
            "ativo": True
        }
        form = InstituicaoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        instituicao = form.save()
        
        # Verifica se o CNPJ e o telefone foram salvos sem caracteres especiais (apenas dígitos)
        self.assertEqual(instituicao.cnpj, "98765432000110")
        self.assertEqual(instituicao.telefone, "8633221122")
        self.assertEqual(instituicao.nome, "IFPI Campus Parnaíba")

    def test_instituicao_form_cnpj_duplicado(self):
        """Testa se o formulário rejeita a criação caso o CNPJ já exista no banco de dados."""
        form_data = {
            "cnpj": "12345678000195",  # Mesmo CNPJ da instituição criada no setUp
            "nome": "Outro Campus com mesmo CNPJ",
            "endereco": "Outro Endereço",
            "telefone": "86999998888",
            "email": "outro@ifpi.edu.br",
            "ativo": True
        }
        form = InstituicaoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn("cnpj", form.errors)
        self.assertEqual(form.errors["cnpj"][0], "Já existe uma instituição cadastrada com este CNPJ.")

    def test_instituicao_form_telefone_opcional(self):
        """Testa se o formulário aceita telefone em branco/vazio sem disparar erros."""
        form_data = {
            "cnpj": "11222333000144",
            "nome": "Campus Sem Telefone",
            "endereco": "Rua Principal",
            "telefone": "",  # Vazio
            "email": "semtelefone@ifpi.edu.br",
            "ativo": True
        }
        form = InstituicaoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        inst = form.save()
        self.assertEqual(inst.telefone, "")

    # ==========================================
    # Testes para o InstituicaoUpdateForm (Edição)
    # ==========================================
    def test_instituicao_update_form_valido(self):
        """Testa a atualização bem-sucedida de dados de uma instituição existente."""
        form_data = {
            "nome": "IFPI Campus Teresina Central - Atualizado",
            "endereco": "Novo Endereço",
            "telefone": "(86) 99888-7766",  # 11 dígitos com máscara
            "email": "novoemail@ifpi.edu.br",
            "ativo": True
        }
        form = InstituicaoUpdateForm(data=form_data, instance=self.instituicao_existente)
        
        self.assertTrue(form.is_valid())
        inst_atualizada = form.save()
        
        self.assertEqual(inst_atualizada.nome, "IFPI Campus Teresina Central - Atualizado")
        self.assertEqual(inst_atualizada.telefone, "86998887766")  # Limpo corretamente

    def test_instituicao_update_form_telefone_invalido(self):
        """Testa se o formulário de atualização valida o tamanho do telefone (deve ter 10 ou 11 dígitos)."""
        form_data = {
            "nome": "IFPI Campus Teresina Central",
            "endereco": "Rua Anísio de Abreu",
            "telefone": "12345",  # Telefone inválido (muito curto)
            "email": "central@ifpi.edu.br",
            "ativo": True
        }
        form = InstituicaoUpdateForm(data=form_data, instance=self.instituicao_existente)
        
        self.assertFalse(form.is_valid())
        self.assertIn("telefone", form.errors)
        self.assertEqual(form.errors["telefone"][0], "Informe um número de telefone válido com DDD (10 ou 11 dígitos).")