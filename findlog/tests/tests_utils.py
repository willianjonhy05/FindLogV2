from unittest.mock import MagicMock, patch
from django.test import RequestFactory, TestCase
from django.core.exceptions import ValidationError
from django.http import Http404

# Substitua 'seu_app' pelo nome real do seu app Django
from findlog.utils import (
    apenas_digitos,
    formatar_cnpj,
    formatar_telefone,
    remover_acentos,
    gerar_slug_unico,
    validar_cnpj,
    gerar_codigo_aleatorio,
    validar_cpf,
    formatar_cpf,
    obter_ip_usuario,
    redirecionar_por_perfil,
    _obter_instituicao_do_servidor,
    gerar_senha_provisoria,
    _obter_instituicao_por_token,
    gerar_qrcode_base64,
)


class UtilsTestCase(TestCase):

    def test_apenas_digitos(self):
        self.assertEqual(apenas_digitos("123.456.789-00"), "12345678900")
        self.assertEqual(apenas_digitos("abc123xyz"), "123")
        self.assertEqual(apenas_digitos(""), "")
        self.assertEqual(apenas_digitos(None), "")

    def test_formatar_cnpj(self):
        self.assertEqual(formatar_cnpj("12345678000195"), "12.345.678/0001-95")
        self.assertEqual(formatar_cnpj("12.345.678/0001-95"), "12.345.678/0001-95")
        self.assertEqual(formatar_cnpj("123"), "123")
        self.assertEqual(formatar_cnpj(""), "")

    def test_formatar_telefone(self):
        self.assertEqual(formatar_telefone("11987654321"), "(11) 98765-4321")
        self.assertEqual(formatar_telefone("1133334444"), "(11) 3333-4444")
        self.assertEqual(formatar_telefone("123"), "123")
        self.assertEqual(formatar_telefone(""), "")

    def test_remover_acentos(self):
        self.assertEqual(remover_acentos("Álvaro d'Ávila, pão e café"), "Alvaro d'Avila, pao e cafe")
        self.assertEqual(remover_acentos(""), "")

    def test_gerar_slug_unico(self):
        # Mockando a classe do model e o queryset para evitar dependência de banco de dados real neste teste
        mock_model = MagicMock()
        mock_queryset = MagicMock()
        mock_queryset.exists.side_effect = [True, False]  # Simula que o primeiro slug já existe, mas o segundo com '-2' está livre
        mock_model.objects.filter.return_value = mock_queryset

        instancia = MagicMock()
        instancia.pk = None
        instancia.nome = "Teste de Slug"

        slug = gerar_slug_unico(mock_model, instancia, campo_origem="nome", campo_slug="slug")
        self.assertEqual(slug, "teste-de-slug-2")

    def test_validar_cnpj_valido_e_invalido(self):
        # Tamanho válido não deve lançar ValidationError de tamanho
        try:
            validar_cnpj("12.345.678/0001-95")
        except ValidationError:
            self.fail("validar_cnpj lançou ValidationError inesperado para 14 dígitos.")

        # Tamanho inválido deve lançar ValidationError
        with self.assertRaises(ValidationError):
            validar_cnpj("123")

    def test_gerar_codigo_aleatorio(self):
        codigo = gerar_codigo_aleatorio(tamanho=10)
        self.assertEqual(len(codigo), 10)
        
        codigo_custom = gerar_codigo_aleatorio(tamanho=5, caracteres="ABC")
        self.assertEqual(len(codigo_custom), 5)
        for char in codigo_custom:
            self.assertIn(char, "ABC")

    def test_validar_cpf_invalido(self):
        # Rejeita sequências repetidas
        with self.assertRaises(ValidationError):
            validar_cpf("11111111111")
        
        # Rejeita tamanho incorreto
        with self.assertRaises(ValidationError):
            validar_cpf("123456789")

    def test_formatar_cpf(self):
        self.assertEqual(formatar_cpf("12345678901"), "123.456.789-01")
        self.assertEqual(formatar_cpf("123"), "123")
        self.assertEqual(formatar_cpf(""), "")

    def test_obter_ip_usuario(self):
        factory = RequestFactory()
        
        # Testa prioridade do HTTP_X_FORWARDED_FOR
        request1 = factory.get("/", HTTP_X_FORWARDED_FOR="203.0.113.195, 70.41.3.18")
        self.assertEqual(obter_ip_usuario(request1), "203.0.113.195")

        # Testa fallback para REMOTE_ADDR quando HTTP_X_FORWARDED_FOR estiver ausente
        request2 = factory.get("/")
        request2.META["REMOTE_ADDR"] = "127.0.0.1"
        self.assertEqual(obter_ip_usuario(request2), "127.0.0.1")

    @patch("findlog.utils.redirect")
    def test_redirecionar_por_perfil_com_next(self, mock_redirect):
        factory = RequestFactory()
        request = factory.get("/?next=/dashboard/personalizado/")
        usuario = MagicMock()
        
        redirecionar_por_perfil(request, usuario)
        mock_redirect.assert_called_once_with("/dashboard/personalizado/")

    def test_obter_instituicao_do_servidor(self):
        request = MagicMock()
        
        # Cenário 1: Encontra através do relacionamento servidor
        request.user.servidor.instituicao = "Instituicao A"
        self.assertEqual(_obter_instituicao_do_servidor(request), "Instituicao A")

        # Cenário 2: Atributo servidor gera AttributeError, busca direto no user
        del request.user.servidor
        request.user.instituicao = "Instituicao B"
        self.assertEqual(_obter_instituicao_do_servidor(request), "Instituicao B")

        # Cenário 3: Nenhum dos atributos existe
        del request.user.instituicao
        self.assertIsNone(_obter_instituicao_do_servidor(request))

    def test_gerar_senha_provisoria(self):
        senha = gerar_senha_provisoria(tamanho=12)
        self.assertEqual(len(senha), 12)
        self.assertIsInstance(senha, str)

    @patch("findlog.models.Instituicao")
    def test_obter_instituicao_por_token_valido(self, mock_instituicao_class):
        mock_inst = MagicMock()
        mock_instituicao_class.obter_por_token.return_value = mock_inst
        
        resultado = _obter_instituicao_por_token("token_valido")
        self.assertEqual(resultado, mock_inst)

    @patch("findlog.models.Instituicao")
    def test_obter_instituicao_por_token_invalido(self, mock_instituicao_class):
        mock_instituicao_class.obter_por_token.return_value = None
        
        with self.assertRaises(Http404):
            _obter_instituicao_por_token("token_invalido")

    def test_gerar_qrcode_base64(self):
        qrcode_str = gerar_qrcode_base64("https://exemplo.com")
        self.assertTrue(qrcode_str.startswith("data:image/png;base64,"))