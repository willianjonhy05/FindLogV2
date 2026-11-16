from django.test import TestCase
from findlog.models import Sala, Instituicao


class SalaModelTestCase(TestCase):

    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI",
            endereco="Centro",
            email="ifpi@edu.br"
        )

    def test_criacao_sala_e_geracao_codigo(self):
        """Testa se a sala é criada, se o código é gerado automaticamente e o telefone sanitizado."""
        sala = Sala.objects.create(
            instituicao=self.instituicao,
            predio="Bloco A",
            andar="1º",
            nome="Laboratório de Informática",
            telefone="(86) 3215-5000",
            sala_de_aula=False,
            laboratorio=True
        )

        # O prefixo deve pegar as primeiras letras de "Laboratorio de Informatica" -> LAB + 000
        self.assertEqual(sala.codigo, "LAB000")
        self.assertEqual(sala.telefone, "8632155000")
        self.assertEqual(sala.telefone_formatado, "(86) 3215-5000")
        self.assertTrue(sala.laboratorio)
        self.assertFalse(sala.sala_de_aula)

    def test_geracao_codigo_unico_para_mesmo_prefixo(self):
        """Testa se salas com nomes de prefixos iguais incrementam a numeração corretamente (ex: SAL000, SAL001)."""
        sala1 = Sala.objects.create(
            predio="Bloco B",
            andar="Térreo",
            nome="Sala 101"
        )
        sala2 = Sala.objects.create(
            predio="Bloco B",
            andar="Térreo",
            nome="Sala 102"
        )

        # "Sala" gera o prefixo SAL
        self.assertEqual(sala1.codigo, "SAL000")
        self.assertEqual(sala2.codigo, "SAL001")

    def test_str_representation(self):
        """Testa o método __str__ da sala."""
        sala = Sala(codigo="AUD000", nome="Auditório Central")
        self.assertEqual(str(sala), "AUD000 - Auditório Central")

        # Caso por algum motivo o código esteja vazio
        sala_sem_codigo = Sala(codigo="", nome="Auditório")
        self.assertEqual(str(sala_sem_codigo), "Auditório")

    def test_ordenacao_padrao(self):
        """Testa se a ordenação segue prédios, andares e nomes (Meta ordering)."""
        s1 = Sala.objects.create(predio="Bloco B", andar="1º", nome="Sala B")
        s2 = Sala.objects.create(predio="Bloco A", andar="1º", nome="Sala A")
        s3 = Sala.objects.create(predio="Bloco A", andar="2º", nome="Sala C")

        salas = list(Sala.objects.all())
        # Ordem esperada: Bloco A (1º Andar), Bloco A (2º Andar), Bloco B (1º Andar)
        self.assertEqual(salas[0], s2)
        self.assertEqual(salas[1], s3)
        self.assertEqual(salas[2], s1)