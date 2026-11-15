import os
import sys
from datetime import timedelta
import django
from django.utils import timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")  # Ajuste "setup.settings" se necessário
django.setup()

from findlog.models import Contato


CONTATOS_DADOS = [
    {
        "nome": "Mariana Costa Silva",
        "email": "mariana.costa@email.com",
        "assunto": Contato.Assuntos.DUVIDA,
        "telefone": "86998112233",
        "mensagem": "Perdi uma garrafa térmica azul no bloco B ontem à tarde. Como faço para acompanhar se já foi cadastrada no sistema?",
        "ip_contato": "177.38.102.14",
    },
    {
        "nome": "Lucas Andrade Lima",
        "email": "lucas.andrade@empresa.com.br",
        "assunto": Contato.Assuntos.ORCAMENTO,
        "telefone": "86988451290",
        "mensagem": "Gostaria de solicitar um orçamento para implantar o FindLog em uma rede com 4 escolas particulares em Teresina.",
        "ip_contato": "189.45.210.88",
    },
    {
        "nome": "Fernanda Oliveira Souza",
        "email": "fernanda.souza@ifpi.edu.br",
        "assunto": Contato.Assuntos.ELOGIO,
        "telefone": "86999345678",
        "mensagem": "Parabéns pela iniciativa! Recuperei minha carteira de estudante em menos de duas horas graças ao aviso na plataforma.",
        "ip_contato": "200.129.43.19",
    },
    {
        "nome": "Carlos Eduardo Mendes",
        "email": "carlos.mendes@gmail.com",
        "assunto": Contato.Assuntos.SUGESTAO,
        "telefone": "86994127890",
        "mensagem": "Seria ótimo se o sistema enviasse uma notificação por e-mail sempre que um item novo fosse cadastrado na minha categoria de interesse.",
        "ip_contato": "179.184.55.102",
    },
    {
        "nome": "Beatriz Nogueira Rocha",
        "email": "bia.nogueira@hotmail.com",
        "assunto": Contato.Assuntos.RECLAMACAO,
        "telefone": "86981234567",
        "mensagem": "Enviei uma reivindicação há três dias e o status ainda consta como pendente. Gostaria de um retorno da coordenação.",
        "ip_contato": "191.242.11.77",
    },
    {
        "nome": "Instituto Educacional Horizonte",
        "email": "diretoria@colegiohorizonte.com.br",
        "assunto": Contato.Assuntos.PARCERIA,
        "telefone": "8632218899",
        "mensagem": "Temos interesse em firmar parceria institucional para utilizar o módulo de achados e perdidos em nossos dois campi.",
        "ip_contato": "187.108.90.41",
    },
    {
        "nome": "Rafael Gomes Pereira",
        "email": "rafael.gp@outlook.com",
        "assunto": Contato.Assuntos.DUVIDA,
        "telefone": "86995674321",
        "mensagem": "Quais documentos preciso levar na recepção para retirar um carregador de notebook aprovado na minha reivindicação?",
        "ip_contato": "177.92.14.205",
    },
    {
        "nome": "Juliana Martins Alencar",
        "email": "juliana.alencar@ufpi.edu.br",
        "assunto": Contato.Assuntos.SUGESTAO,
        "telefone": "86999110022",
        "mensagem": "Sugiro adicionar um campo opcional de cor predominante nos filtros rápidos da tela inicial do usuário.",
        "ip_contato": "200.137.160.50",
    },
    {
        "nome": "Pedro Henrique Barros",
        "email": "pedro.barros@yahoo.com.br",
        "assunto": Contato.Assuntos.OUTRO,
        "telefone": "86988776655",
        "mensagem": "Encontrei um molho de chaves próximo ao estacionamento externo e entreguei na portaria principal hoje às 10h.",
        "ip_contato": "186.215.33.91",
    },
    {
        "nome": "Camila Ribeiro Castro",
        "email": "camila.castro@clinicasaude.com.br",
        "assunto": Contato.Assuntos.ORCAMENTO,
        "telefone": "8632324455",
        "mensagem": "Atendemos cerca de 600 pacientes por dia e gostaríamos de saber os planos disponíveis para clínicas e hospitais.",
        "ip_contato": "189.12.78.134",
    },
    {
        "nome": "Thiago Vasconcelos Dias",
        "email": "thiago.dias@gmail.com",
        "assunto": Contato.Assuntos.ELOGIO,
        "telefone": "86994556677",
        "mensagem": "Interface muito limpa, rápida e fácil de usar pelo celular. Facilitou bastante o trabalho da nossa equipe.",
        "ip_contato": "179.99.201.18",
    },
    {
        "nome": "Amanda Torres Sampaio",
        "email": "amanda.sampaio@uespi.br",
        "assunto": Contato.Assuntos.DUVIDA,
        "telefone": "86998223344",
        "mensagem": "Minha conta está vinculada ao campus Poeta Torquato Neto. Posso consultar itens de outras unidades também?",
        "ip_contato": "200.23.89.112",
    },
    {
        "nome": "Rodrigo Ferreira Carvalho",
        "email": "rodrigo.carvalho@techpiau.com.br",
        "assunto": Contato.Assuntos.PARCERIA,
        "telefone": "86999887766",
        "mensagem": "Somos uma empresa de totens de autoatendimento e gostaríamos de conversar sobre integração com o FindLog.",
        "ip_contato": "177.154.62.39",
    },
    {
        "nome": "Larissa Monteiro Cunha",
        "email": "larissa.cunha@gmail.com",
        "assunto": Contato.Assuntos.RECLAMACAO,
        "telefone": "86981998877",
        "mensagem": "Tentei anexar uma foto da nota fiscal na reivindicação pelo navegador antigo e demorou bastante para carregar.",
        "ip_contato": "191.54.180.22",
    },
    {
        "nome": "Gustavo Henrique Moura",
        "email": "gustavo.moura@email.com",
        "assunto": Contato.Assuntos.DUVIDA,
        "telefone": "",
        "mensagem": "Por quanto tempo os objetos encontrados ficam armazenados na instituição antes de serem doados ou descartados?",
        "ip_contato": "187.44.19.63",
    },
    {
        "nome": "Patrícia Lima Azevedo",
        "email": "patricia.azevedo@shoppingcentro.com.br",
        "assunto": Contato.Assuntos.ORCAMENTO,
        "telefone": "8632189000",
        "mensagem": "Precisamos digitalizar o setor de Achados e Perdidos do nosso centro comercial. Podemos agendar uma demonstração?",
        "ip_contato": "189.84.122.47",
    },
    {
        "nome": "Bruno César Farias",
        "email": "bruno.farias@gmail.com",
        "assunto": Contato.Assuntos.SUGESTAO,
        "telefone": "86994001122",
        "mensagem": "Seria interessante gerar um comprovante em PDF com QR Code quando a reivindicação for aprovada para retirada.",
        "ip_contato": "177.201.88.15",
    },
    {
        "nome": "Vanessa Brito Magalhães",
        "email": "vanessa.brito@hotmail.com",
        "assunto": Contato.Assuntos.ELOGIO,
        "telefone": "86998765432",
        "mensagem": "Atendimento excelente da equipe da coordenação ao validar meus documentos e devolver meus óculos de grau.",
        "ip_contato": "179.110.45.90",
    },
    {
        "nome": "Felipe Augusto Teixeira",
        "email": "felipe.teixeira@outlook.com",
        "assunto": Contato.Assuntos.OUTRO,
        "telefone": "86988119922",
        "mensagem": "Gostaria de atualizar meu e-mail institucional no cadastro pois mudei de curso neste semestre.",
        "ip_contato": "186.192.74.31",
    },
    {
        "nome": "Secretaria Municipal de Cultura",
        "email": "eventos@cultura.teresina.pi.gov.br",
        "assunto": Contato.Assuntos.PARCERIA,
        "telefone": "8632157800",
        "mensagem": "Buscamos uma solução para gerenciar objetos perdidos durante os grandes eventos culturais e festivais da cidade.",
        "ip_contato": "200.142.98.10",
    },
    {
        "nome": "Renata Pinheiro Lemos",
        "email": "renata.lemos@gmail.com",
        "assunto": Contato.Assuntos.DUVIDA,
        "telefone": "86995123498",
        "mensagem": "Outra pessoa pode retirar o item aprovado por mim caso eu envie uma autorização por escrito?",
        "ip_contato": "191.180.23.64",
    },
    {
        "nome": "Diego Santana Vieira",
        "email": "diego.vieira@empresa.com",
        "assunto": Contato.Assuntos.RECLAMACAO,
        "telefone": "86999443322",
        "mensagem": "O horário de funcionamento da sala de retirada não estava visível na descrição do local.",
        "ip_contato": "177.66.140.82",
    },
    {
        "nome": "Aline Cardoso Mesquita",
        "email": "aline.mesquita@gmail.com",
        "assunto": Contato.Assuntos.SUGESTAO,
        "telefone": "86981332211",
        "mensagem": "Adicionar um botão de compartilhamento direto do link do item no WhatsApp ajudaria muito a avisar colegas de turma.",
        "ip_contato": "189.33.175.19",
    },
    {
        "nome": "Marcelo Nunes Cavalcante",
        "email": "marcelo.cavalcante@academiafit.com.br",
        "assunto": Contato.Assuntos.ORCAMENTO,
        "telefone": "86998554433",
        "mensagem": "Temos 3 unidades de academia e acumulamos muitos squeezes, toalhas e fones. Como funciona a contratação do sistema?",
        "ip_contato": "187.75.204.11",
    },
    {
        "nome": "Helena Sousa Marques",
        "email": "helena.marques@gmail.com",
        "assunto": Contato.Assuntos.ELOGIO,
        "telefone": "86994887711",
        "mensagem": "Sistema muito organizado e transparente. Dá muita segurança saber exatamente em qual sala o objeto está guardado.",
        "ip_contato": "179.222.16.74",
    },
]


def executar():
    criados = 0
    existentes = 0
    agora = timezone.now()

    for idx, dados in enumerate(CONTATOS_DADOS):
        contato, criado = Contato.objects.get_or_create(
            email=dados["email"],
            assunto=dados["assunto"],
            defaults={
                "nome": dados["nome"],
                "telefone": dados["telefone"],
                "mensagem": dados["mensagem"],
                "ip_contato": dados["ip_contato"],
            },
        )
        if criado:
            # Distribui as datas nas últimas semanas para testar paginação e ordenação (-data)
            data_retroativa = agora - timedelta(days=idx, hours=idx * 2)
            Contato.objects.filter(pk=contato.pk).update(data=data_retroativa)
            criados += 1
            print(f"[+] Contato criado: {contato.nome} ({contato.get_assunto_display()})")
        else:
            existentes += 1
            print(f"[=] Já existia: {contato.nome} ({contato.email})")

    print(f"\nResumo Contatos -> Criados: {criados} | Já existentes: {existentes}")


if __name__ == "__main__":
    executar()