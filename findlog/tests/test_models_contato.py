from django.test import TestCase
from findlog.models import Contato

import time

class ContatoModelTestCase(TestCase):

    def test_criacao_contato_e_sanitizacao_telefone(self):
        """Testa a criação de um contato e se o telefone é sanitizado (apenas dígitos) ao salvar."""
        contato = Contato.objects.create(
            nome="Maria Silva",
            email="maria@exemplo.com",
            assunto=Contato.Assuntos.DUVIDA,
            telefone="(11) 98765-4321",
            mensagem="Preciso de ajuda com um item.",
            ip_contato="192.168.1.10"
        )
        
        # Verifica se o UUID foi gerado automaticamente
        self.assertTrue(contato.uuid)
        
        # O telefone deve ser salvo apenas com dígitos graças ao método _sanitizar_campos()
        self.assertEqual(contato.telefone, "11987654321")
        
        # A property telefone_formatado deve retornar a máscara correta
        self.assertEqual(contato.telefone_formatado, "(11) 98765-4321")

    def test_str_representation_com_e_sem_nome(self):
        """Testa o método __str__ quando há nome e quando o nome é nulo/vazio."""
        contato1 = Contato.objects.create(nome="João", assunto=Contato.Assuntos.ELOGIO)
        contato2 = Contato.objects.create(nome=None, assunto=Contato.Assuntos.SUGESTAO)

        self.assertEqual(str(contato1), "João")
        self.assertEqual(str(contato2), "Contato sem nome")

    def test_ordenacao_padrao_contato(self):
        """Testa se a ordenação padrão é por data decrescente (-data)."""
        c1 = Contato.objects.create(nome="Primeiro", assunto=Contato.Assuntos.OUTRO)
        time.sleep(0.01)
        c2 = Contato.objects.create(nome="Segundo", assunto=Contato.Assuntos.OUTRO)

        contatos = list(Contato.objects.all())
        # Como a ordenação é -data, o contato criado por último (mais recente) vem primeiro
        self.assertEqual(contatos[0].nome, "Segundo")
        self.assertEqual(contatos[1].nome, "Primeiro")