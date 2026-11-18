from django.test import TestCase
from django.core.exceptions import ValidationError
from findlog.models import Instituicao


class InstituicaoModelTestCase(TestCase):

    def test_criacao_instituicao_com_sucesso_e_sanitizacao(self):
        """Testa se a instituição é criada corretamente e se CNPJ e telefone são sanitizados."""
        instituicao = Instituicao.objects.create(
            cnpj="12.345.678/0001-95",
            nome="Instituto Federal do Piauí",
            endereco="Rua Anísio de Abreu, 3289",
            telefone="(86) 3215-6000",
            email="contato@ifpi.edu.br",
            ativo=True
        )

        # Verifica se CNPJ e telefone foram limpos (apenas dígitos)
        self.assertEqual(instituicao.cnpj, "12345678000195")
        self.assertEqual(instituicao.telefone, "8632156000")

        # Verifica as propriedades formatadas
        self.assertEqual(instituicao.cnpj_formatado, "12.345.678/0001-95")
        self.assertEqual(instituicao.telefone_formatado, "(86) 3215-6000")

    def test_validacao_cnpj_invalido_durante_criacao(self):
        """Testa se um CNPJ inválido ou com tamanho incorreto dispara ValidationError no save/full_clean."""
        instituicao = Instituicao(
            cnpj="123",  # Tamanho inválido
            nome="Instituição Inválida",
            endereco="Rua Fictícia",
            email="teste@teste.com"
        )

        with self.assertRaises(ValidationError):
            instituicao.full_clean()

    def test_token_convite_e_obter_por_token_valido(self):
        """Testa a geração do token assinado e a recuperação correta da instituição pelo token."""
        instituicao = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina",
            endereco="Centro",
            email="teresina@ifpi.edu.br",
            ativo=True
        )

        token = instituicao.token_convite
        self.assertTrue(token)

        # Recupera a instituição usando o token válido
        inst_recuperada = Instituicao.obter_por_token(token)
        self.assertEqual(inst_recuperada, instituicao)

    def test_obter_por_token_invalido_ou_adulterado(self):
        """Testa se o método retorna None ao receber um token corrompido ou falso."""
        inst_invalida = Instituicao.obter_por_token("token-falso-ou-adulterado")
        self.assertIsNone(inst_invalida)

    def test_obter_por_token_instituicao_inativa(self):
        """Testa se o método retorna None se a instituição associada ao token estiver inativa."""
        instituicao = Instituicao.objects.create(
            cnpj="74580881000101",
            nome="Instituição Inativa",
            endereco="Av. Central",
            email="inativa@ifpi.edu.br",
            ativo=False
        )

        token = instituicao.token_convite
        inst_recuperada = Instituicao.obter_por_token(token)
        self.assertIsNone(inst_recuperada)

    def test_str_representation(self):
        """Testa o método __str__ da instituição."""
        instituicao = Instituicao.objects.create(
            cnpj="08886436000131",
            nome="Reitoria IFPI",
            endereco="Praça da Liberdade",
            email="reitoria@ifpi.edu.br"
        )
        self.assertEqual(str(instituicao), "Reitoria IFPI")