import os
import sys
from datetime import timedelta
import django
from django.utils import timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")  # Ajuste "setup.settings" se necessário
django.setup()

from findlog.models import Item, Perfil, Sala, Reivindicacao


CENARIOS_REIVINDICACAO = [
    (
        Reivindicacao.StatusReivindicacao.PENDENTE,
        "Perdi essa garrafa logo após a aula de banco de dados. Ela tem um adesivo pequeno de foguete perto da base.",
        "",
    ),
    (
        Reivindicacao.StatusReivindicacao.PENDENTE,
        "Minha carteira marrom caiu da mochila ontem. Dentro há um cartão com meu nome impresso e minha foto 3x4.",
        "",
    ),
    (
        Reivindicacao.StatusReivindicacao.EM_ANALISE,
        "O estojo de fones é meu, o número de série na tampa interna termina com 84B. Posso mostrar o pareamento no meu celular.",
        "Solicitação em verificação junto à equipe do turno vespertino.",
    ),
    (
        Reivindicacao.StatusReivindicacao.EM_ANALISE,
        "Esqueci o carregador na tomada da última bancada do laboratório. Tem uma fita isolante enrolada perto do plugue.",
        "Conferindo características físicas do cabo armazenado.",
    ),
    (
        Reivindicacao.StatusReivindicacao.APROVADA,
        "O molho tem duas chaves Yale douradas e uma chave tetra, além do chaveiro metálico.",
        "Propriedade confirmada. Compareça à sala indicada com documento de identificação com foto.",
    ),
    (
        Reivindicacao.StatusReivindicacao.APROVADA,
        "Meu óculos de grau ficou sobre a mesa da biblioteca. A haste esquerda está levemente frouxa e o estojo tem um pano azul.",
        "Reivindicação aprovada! Retirada liberada no horário comercial.",
    ),
    (
        Reivindicacao.StatusReivindicacao.REJEITADA,
        "Acredito que essa calculadora seja minha, perdi uma parecida na semana passada.",
        "As características informadas e a marcação no verso não conferem com o objeto guardado.",
    ),
    (
        Reivindicacao.StatusReivindicacao.CONCLUIDA,
        "Mochila preta com um caderno de capa azul e um pendrive no bolso frontal.",
        "Devolução realizada presencialmente mediante assinatura do termo de entrega.",
    ),
    (
        Reivindicacao.StatusReivindicacao.CONCLUIDA,
        "Guarda-chuva azul marinho que deixei encostado perto da porta do auditório após o evento.",
        "Item entregue ao proprietário após conferência.",
    ),
    (
        Reivindicacao.StatusReivindicacao.PENDENTE,
        "Meu relógio soltou a trava da pulseira durante a atividade física no pátio.",
        "",
    ),
    (
        Reivindicacao.StatusReivindicacao.PENDENTE,
        "Esqueci meu jaleco na cadeira do laboratório de informática ontem à noite.",
        "",
    ),
    (
        Reivindicacao.StatusReivindicacao.EM_ANALISE,
        "O livro de Engenharia de Software tem meu nome escrito a lápis na primeira folha.",
        "Verificando assinatura na folha de rosto do exemplar.",
    ),
    (
        Reivindicacao.StatusReivindicacao.APROVADA,
        "O pendrive de 32GB contém uma pasta chamada 'TCC_2026' e slides de apresentação.",
        "Conteúdo confirmado. Disponível para retirada na coordenação.",
    ),
    (
        Reivindicacao.StatusReivindicacao.REJEITADA,
        "Perdi meu celular azul no corredor hoje cedo.",
        "O modelo e o papel de parede de bloqueio não correspondem ao aparelho encontrado.",
    ),
    (
        Reivindicacao.StatusReivindicacao.CONCLUIDA,
        "Caderno de 10 matérias com etiqueta vermelha na capa e anotações de Python.",
        "Devolvido ao aluno na secretaria.",
    ),
    (
        Reivindicacao.StatusReivindicacao.PENDENTE,
        "Deixei meu estojo verde água na carteira da fila do meio.",
        "",
    ),
    (
        Reivindicacao.StatusReivindicacao.EM_ANALISE,
        "Meu cartão de passe estudantil caiu perto da entrada principal hoje pela manhã.",
        "Validando número do cartão com a matrícula do solicitante.",
    ),
    (
        Reivindicacao.StatusReivindicacao.PENDENTE,
        "Esqueci meu boné preto na arquibancada após o intervalo.",
        "",
    ),
    (
        Reivindicacao.StatusReivindicacao.APROVADA,
        "O power bank cinza tem um pequeno arranhão próximo à entrada USB-C.",
        "Aprovado para retirada. Apresentar documento oficial.",
    ),
    (
        Reivindicacao.StatusReivindicacao.PENDENTE,
        "Deixei meu casaco de moletom cinza pendurado na cadeira da sala 101.",
        "",
    ),
]


def executar():
    itens = list(Item.objects.filter(status=Item.StatusItem.ENCONTRADO).order_by("data_registro"))
    if not itens:
        print("[!] Nenhum item disponível encontrado. Execute 'popular_itens.py' primeiro.")
        return

    usuarios_comuns = list(Perfil.objects.filter(tipo=Perfil.TipoUsuario.USUARIO, ativo=True))
    if not usuarios_comuns:
        print("[!] Nenhum usuário comum ativo encontrado. Execute 'popular_usuarios.py' primeiro.")
        return

    criadas = 0
    existentes = 0
    agora = timezone.now()

    total_gerar = min(len(CENARIOS_REIVINDICACAO), len(itens))

    for idx in range(total_gerar):
        item = itens[idx]
        inst = item.instituicao
        status_reiv, pedido_txt, resposta_txt = CENARIOS_REIVINDICACAO[idx]

        # Prioriza um usuário vinculado à mesma instituição do item
        usuarios_da_inst = [u for u in usuarios_comuns if u.instituicao.filter(pk=inst.pk).exists()]
        autor = (
            usuarios_da_inst[idx % len(usuarios_da_inst)]
            if usuarios_da_inst
            else usuarios_comuns[idx % len(usuarios_comuns)]
        )

        # Garante que o autor tenha vínculo com a instituição do item para consistência
        autor.instituicao.add(inst)

        # Busca um servidor da instituição caso a reivindicação já tenha sido analisada
        servidor_resp = None
        sala_devolucao = None
        if status_reiv != Reivindicacao.StatusReivindicacao.PENDENTE:
            servidor_resp = (
                Perfil.objects.filter(
                    tipo=Perfil.TipoUsuario.SERVIDOR,
                    ativo=True,
                    instituicao=inst,
                ).first()
                or Perfil.objects.filter(is_superuser=True).first()
            )
            sala_devolucao = (
                item.local_guardado
                or Sala.objects.filter(instituicao=inst, ativa=True).first()
            )

        reiv, criada = Reivindicacao.objects.get_or_create(
            autor=autor,
            item=item,
            instituicao=inst,
            defaults={
                "pedido": pedido_txt,
                "status": status_reiv,
                "resposta_admin": resposta_txt,
                "responsavel_admin": servidor_resp,
                "local_devolucao": sala_devolucao,
                "data_devolucao": agora - timedelta(hours=idx) if status_reiv == Reivindicacao.StatusReivindicacao.CONCLUIDA else None,
            },
        )

        if criada:
            data_retroativa = agora - timedelta(days=idx // 2, hours=(idx % 12) + 1)
            Reivindicacao.objects.filter(pk=reiv.pk).update(data=data_retroativa)

            # Se a reivindicação já foi concluída, atualiza o Item para DEVOLVIDO
            if status_reiv == Reivindicacao.StatusReivindicacao.CONCLUIDA:
                Item.objects.filter(pk=item.pk).update(
                    status=Item.StatusItem.DEVOLVIDO,
                    dono=autor,
                    data_devolucao=agora - timedelta(hours=idx),
                )

            criadas += 1
            print(
                f"[+] Reivindicação #{reiv.protocolo} criada | Item: {item.nome} | "
                f"Status: {reiv.get_status_display()} | Solicitante: {autor.nome}"
            )
        else:
            existentes += 1
            print(f"[=] Já existia reivindicação de {autor.nome} para {item.nome}")

    print(f"\nResumo Reivindicações -> Criadas: {criadas} | Já existentes: {existentes}")


if __name__ == "__main__":
    executar()