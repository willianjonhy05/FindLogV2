from datetime import date
from django.test import TestCase
from findlog.models import Perfil, Instituicao, VinculoInstituicao


class PerfilModelTestCase(TestCase):

    def setUp(self):
        # Cria uma instituição válida para testes que exijam relacionamento
        self.instituicao = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI",
            endereco="Centro",
            email="ifpi@edu.br"
        )

    def test_criacao_perfil_com_sucesso_e_sanitizacao(self):
        """Testa a criação de um perfil e a sanitização de CPF e telefone."""
        perfil = Perfil.objects.create_user(
            username="william",  # <-- Adicionado aqui
            email="william@exemplo.com",
            password="senha123",
            nome="William Sousa",
            cpf="123.456.789-01",
            telefone="(86) 99999-8888"
        )

        self.assertEqual(perfil.cpf, "12345678901")
        self.assertEqual(perfil.telefone, "86999998888")
        self.assertEqual(perfil.cpf_formatado, "123.456.789-01")
        self.assertEqual(perfil.telefone_formatado, "(86) 99999-8888")
        self.assertEqual(perfil.primeiro_nome, "William")
        self.assertTrue(perfil.username)

    def test_geracao_automatica_username(self):
        """Testa se o username é gerado automaticamente baseado no email quando não fornecido."""
        perfil = Perfil.objects.create(
            email="joao.silva@exemplo.com",
            cpf="98765432100",
            nome="João Silva"
        )
        self.assertTrue(perfil.username.startswith("joao.silva"))

    def test_calculo_idade(self):
        """Testa o cálculo da idade com base na data de nascimento."""
        hoje = date.today()
        # Data de nascimento simulando exatamente 25 anos completados hoje
        nascimento = date(hoje.year - 25, hoje.month, hoje.day)
        
        perfil = Perfil(
            email="idade@exemplo.com",
            cpf="11144477735",
            data_nascimento=nascimento
        )
        self.assertEqual(perfil.idade, 25)

        # Sem data de nascimento
        perfil_sem_data = Perfil()
        self.assertIsNone(perfil_sem_data.idade)

    def test_regras_tipo_usuario_e_permissoes(self):
        """Testa se a definição do tipo de usuário ajusta corretamente is_superuser e is_staff."""
        # Perfil Administrador deve ganhar superuser e staff
        admin_user = Perfil.objects.create(
            email="admin@exemplo.com",
            cpf="22233344455",
            tipo=Perfil.TipoUsuario.ADMINISTRADOR
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)

        # Perfil Servidor ou Usuário comum não devem ter privilégios administrativos
        servidor_user = Perfil.objects.create(
            email="servidor@exemplo.com",
            cpf="55544433322",
            tipo=Perfil.TipoUsuario.SERVIDOR
        )
        self.assertFalse(servidor_user.is_superuser)
        self.assertFalse(servidor_user.is_staff)

    def test_str_representation(self):
        """Testa o método __str__ (retorna nome se houver, senão email)."""
        p1 = Perfil(nome="Ana Maria", email="ana@exemplo.com", cpf="12312312300")
        p2 = Perfil(nome=None, email="semnome@exemplo.com", cpf="32132132100")

        self.assertEqual(str(p1), "Ana Maria")
        self.assertEqual(str(p2), "semnome@exemplo.com")

    def test_vinculo_instituicao(self):
        """Testa a criação do relacionamento ManyToMany através do modelo intermediário."""
        perfil = Perfil.objects.create(
            email="vinculo@exemplo.com",
            cpf="77788899900",
            nome="Vinculado"
        )
        
        VinculoInstituicao.objects.create(perfil=perfil, instituicao=self.instituicao)
        
        self.assertIn(self.instituicao, perfil.instituicao.all())
        self.assertEqual(perfil.instituicao.first().nome, "IFPI")