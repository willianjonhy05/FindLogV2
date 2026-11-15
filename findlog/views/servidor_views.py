from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from ..forms import ServidorSalaForm, ServidorUpdateSalaForm, ServidorCadastroColegaForm, ServidorItemForm, ServidorAnaliseReivindicacaoForm
from ..models import Perfil, Sala, Categoria, Item, Reivindicacao, Instituicao
from ..decorators import servidor_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.db.models import Q
import re

@servidor_required
def servidor_painel(request):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.get(cnpj=cnpj_sessao)

    if not instituicao:
        messages.error(request, "Você não possui vínculo com nenhuma instituição ativa.")
        return redirect("login")

    # Contagens métricas para os cards do dashboard
    qtde_reivindicacoes = Reivindicacao.objects.filter(instituicao=instituicao).count()
    qtde_itens = Item.objects.filter(instituicao=instituicao).count()
    qtde_usuarios = Perfil.objects.filter(
        instituicao=instituicao,
        tipo=Perfil.TipoUsuario.USUARIO
        ).count()
    qtde_servidores = Perfil.objects.filter(
        instituicao=instituicao, 
        tipo=Perfil.TipoUsuario.SERVIDOR
    ).count()
    qtde_salas = Sala.objects.filter(instituicao=instituicao).count()

    # Opcional: últimos itens registrados para exibição rápida no painel
    ultimos_itens = Item.objects.filter(instituicao=instituicao).select_related(
        "categoria", "local"
    ).order_by("-data_registro")[:5]

    context = {
        "instituicao": instituicao,
        "qtde_reivindicacoes": qtde_reivindicacoes,
        "qtde_itens": qtde_itens,
        "qtde_usuarios": qtde_usuarios,
        "qtde_servidores": qtde_servidores,
        "qtde_salas": qtde_salas,
        "ultimos_itens": ultimos_itens,
    }

    return render(request, "serv/index.html", context)

@servidor_required
def servidor_cadastrar_sala(request):
    usuario = request.user

    # 1. Garante que apenas Servidores (ou Administradores) acessem
    if usuario.tipo != Perfil.TipoUsuario.SERVIDOR and not (usuario.tipo == Perfil.TipoUsuario.ADMINISTRADOR or usuario.is_superuser):
        messages.error(request, "Acesso restrito ao perfil de servidor.")
        return redirect("login")

    # 2. Localiza a instituição ativa do servidor
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    if cnpj_sessao:
        instituicao = usuario.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    # Fallback caso não esteja na sessão: pega a primeira instituição ativa vinculada
    if not instituicao:
        instituicao = usuario.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Você não possui vínculo ativo com nenhuma instituição parceira.")
        return redirect("servidor_painel")

    if request.method == "POST":
        form = ServidorSalaForm(request.POST)
        if form.is_valid():
            sala = form.save(commit=False)
            sala.instituicao = instituicao  # Vincula à instituição do servidor
            sala.ativa = True              # Inicia sempre como ativa
            sala.save()

            messages.success(request, f"Sala '{sala.nome}' cadastrada com sucesso na unidade {instituicao.nome}!")
            return redirect("servidor_listar_salas")

        messages.error(request, "Não foi possível cadastrar a sala. Verifique os dados destacados.")
    else:
        form = ServidorSalaForm()

    context = {
        "form": form,
        "instituicao": instituicao,
    }
    return render(request, "serv/cadastrar_sala.html", context)


@servidor_required
def servidor_listar_salas(request):
    usuario = request.user

    # Identifica a instituição ativa (sessão ou primeiro vínculo ativo)
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    if cnpj_sessao:
        instituicao = usuario.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = usuario.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Você não possui vínculo ativo com nenhuma instituição parceira.")
        return redirect("login")

    # Queryset filtrado exclusivamente pela instituição do servidor
    salas_qs = Sala.objects.filter(instituicao=instituicao).order_by("predio", "andar", "nome")

    # Filtro de Busca
    termo_busca = request.GET.get("q", "").strip()
    if termo_busca:
        salas_qs = salas_qs.filter(
            Q(nome__icontains=termo_busca) |
            Q(predio__icontains=termo_busca) |
            Q(codigo__icontains=termo_busca) |
            Q(andar__icontains=termo_busca)
        )

    # Paginação (10 itens por página)
    paginator = Paginator(salas_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "instituicao": instituicao,
        "page_obj": page_obj,
        "termo_busca": termo_busca,
        "total_salas": paginator.count,
    }
    return render(request, "serv/salas.html", context)

@servidor_required
def servidor_editar_sala(request, codigo):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.get(cnpj=cnpj_sessao)

    if not instituicao:
        messages.error(request, "Vínculo institucional não encontrado para este usuário.")
        return redirect('servidor_painel')

    # Garante que a sala pertence obrigatoriamente à instituição do servidor
    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)

    if request.method == 'POST':
        form = ServidorUpdateSalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            messages.success(request, f'Sala "{sala.nome}" atualizada com sucesso!')
            return redirect('servidor_listar_salas')
    else:
        form = ServidorUpdateSalaForm(instance=sala)

    context = {
        'form': form,
        'sala': sala,
        'instituicao': instituicao,
    }
    return render(request, 'serv/editar_sala.html', context)


@servidor_required
@require_POST
def servidor_alternar_status_sala(request, codigo):
    """
    Alterna o status da sala (ativa/inativa) de forma atômica via requisição POST.
    """
    sala = get_object_or_404(Sala, codigo=codigo)
    
    # Inverte o booleano atual
    sala.ativa = not sala.ativa
    sala.save(update_fields=['ativa'])

    status_str = "ativada" if sala.ativa else "desativada"
    messages.success(request, f"A sala '{sala.nome}' foi {status_str} com sucesso.")

    # Redireciona de volta para a listagem ou para a página anterior
    return redirect(request.META.get('HTTP_REFERER', 'servidor_listar_salas'))

@servidor_required
@require_POST
def servidor_ativar_sala(request, codigo):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.get(cnpj=cnpj_sessao)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect('servidor_painel')

    # Só altera se a sala pertencer à mesma unidade
    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)
    
    if not sala.ativa:
        sala.ativa = True
        sala.save(update_fields=['ativa'])
        messages.success(request, f'A sala "{sala.nome}" foi reativada com sucesso.')
    else:
        messages.info(request, f'A sala "{sala.nome}" já se encontra ativa.')

    return redirect('servidor_listar_salas')


@servidor_required
@require_POST
def servidor_desativar_sala(request, codigo):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.filter(cnpj=cnpj_sessao).first()
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)

    if sala.ativa:
        sala.ativa = False
        sala.save(update_fields=["ativa"])
        messages.success(request, f'A sala "{sala.nome}" foi desativada com sucesso.')
    else:
        messages.info(request, f'A sala "{sala.nome}" já está inativa.')

    return redirect("servidor_detalhar_sala", codigo=sala.codigo)


@servidor_required
@require_POST
def servidor_excluir_sala(request, codigo):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.filter(cnpj=cnpj_sessao).first()
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)
    nome_sala = sala.nome
    sala.delete()

    messages.success(request, f'A sala "{nome_sala}" foi excluída permanentemente.')
    return redirect("servidor_listar_salas")


@servidor_required
def servidor_detalhar_sala(request, codigo):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.get(cnpj=cnpj_sessao)

    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect('servidor_painel')

    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)

    context = {
        "sala": sala
    }

    return render(request, "serv/detalhar_sala.html", context)



@servidor_required
def servidor_listar_itens(request):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.get(cnpj=cnpj_sessao)
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    itens_qs = Item.objects.filter(instituicao=instituicao).select_related(
        "categoria", "local", "local_guardado", "usuario_registro"
    ).order_by("-data_registro")

    # Filtro de busca textual
    q = request.GET.get("q", "").strip()
    if q:
        itens_qs = itens_qs.filter(
            Q(nome__icontains=q) |
            Q(codigo__icontains=q) |
            Q(descricao__icontains=q) |
            Q(marca_ou_modelo__icontains=q) |
            Q(cor__icontains=q)
        )

    # Filtro opcional por Status
    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        itens_qs = itens_qs.filter(status=int(status_filtro))

    paginator = Paginator(itens_qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "titulo": "Todos os Itens Registrados",
        "subtitulo": f"Itens achados e perdidos da unidade: {instituicao.nome}",
        "instituicao": instituicao,
        "page_obj": page_obj,
        "termo_busca": q,
        "status_filtro": status_filtro,
        "status_choices": Item.StatusItem.choices,
        "total_itens": paginator.count,
    }
    return render(request, "serv/listar_itens.html", context)


# ----------------------------------------------------------------------
# 2. LISTAR ITENS POR SALA (Onde foi encontrado ou guardado)
# ----------------------------------------------------------------------
@servidor_required
def servidor_itens_por_sala(request, sala_codigo):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.get(cnpj=cnpj_sessao)

    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    sala = get_object_or_404(Sala, codigo=sala_codigo, instituicao=instituicao)

    # Considera o item associado à sala onde foi achado OU onde está guardado
    itens_qs = Item.objects.filter(
        Q(instituicao=instituicao) & (Q(local=sala) | Q(local_guardado=sala))
    ).select_related("categoria", "local", "local_guardado").order_by("-data_registro")

    q = request.GET.get("q", "").strip()
    if q:
        itens_qs = itens_qs.filter(
            Q(nome__icontains=q) |
            Q(codigo__icontains=q) |
            Q(marca_ou_modelo__icontains=q)
        )

    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        itens_qs = itens_qs.filter(status=int(status_filtro))

    paginator = Paginator(itens_qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "titulo": f"Itens na Sala: {sala.nome}",
        "subtitulo": f"Prédio {sala.predio}, Andar {sala.andar} - {instituicao.nome}",
        "instituicao": instituicao,
        "sala": sala,
        "page_obj": page_obj,
        "termo_busca": q,
        "status_filtro": status_filtro,
        "status_choices": Item.StatusItem.choices,
        "total_itens": paginator.count,
    }
    return render(request, "serv/listar_itens.html", context)


# ----------------------------------------------------------------------
# 3. LISTAR ITENS POR CATEGORIA
# ----------------------------------------------------------------------
@servidor_required
def servidor_itens_por_categoria(request, categoria_id):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.get(cnpj=cnpj_sessao)
    
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    categoria = get_object_or_404(Categoria, pk=categoria_id)

    itens_qs = Item.objects.filter(
        instituicao=instituicao,
        categoria=categoria
    ).select_related("categoria", "local", "local_guardado").order_by("-data_registro")

    q = request.GET.get("q", "").strip()
    if q:
        itens_qs = itens_qs.filter(
            Q(nome__icontains=q) |
            Q(codigo__icontains=q) |
            Q(marca_ou_modelo__icontains=q)
        )

    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        itens_qs = itens_qs.filter(status=int(status_filtro))

    paginator = Paginator(itens_qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "titulo": f"Categoria: {categoria.nome}",
        "subtitulo": f"Itens classificados como '{categoria.nome}' em {instituicao.nome}",
        "instituicao": instituicao,
        "categoria": categoria,
        "page_obj": page_obj,
        "termo_busca": q,
        "status_filtro": status_filtro,
        "status_choices": Item.StatusItem.choices,
        "total_itens": paginator.count,
    }
    return render(request, "serv/listar_itens.html", context)


@servidor_required
def servidor_cadastrar_usuario(request):
    usuario_logado = request.user

    # 1. Identifica a instituição do servidor
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    if cnpj_sessao:
        instituicao = usuario_logado.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = usuario_logado.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Você não está vinculado a nenhuma instituição ativa.")
        return redirect("login")

    # 2. Processa o envio do formulário
    if request.method == "POST":
        dados_post = request.POST.copy()

        # Higienização de segurança antes da validação do form
        if "cpf" in dados_post and dados_post["cpf"]:
            dados_post["cpf"] = re.sub(r"\D", "", dados_post["cpf"])
        if "telefone" in dados_post and dados_post["telefone"]:
            dados_post["telefone"] = re.sub(r"\D", "", dados_post["telefone"])

        form = ServidorCadastroColegaForm(dados_post, instituicao=instituicao)

        if form.is_valid():
            novo_usuario = form.save()
            tipo_label = novo_usuario.get_tipo_display()
            messages.success(
                request, 
                f"{tipo_label} '{novo_usuario.nome or novo_usuario.username}' cadastrado(a) com sucesso!"
            )
            return redirect("servidor_listar_usuarios")

        messages.error(request, "Verifique os erros nos campos antes de continuar.")
    else:
        form = ServidorCadastroColegaForm(instituicao=instituicao)

    context = {
        "form": form,
        "instituicao": instituicao,
    }
    return render(request, "serv/cadastrar_usuario.html", context)


def servidor_usuarios_instituicao(request):
    """
    Lista de todos os usuários da instituição
    """
    pass


def servidor_visualizar_usuario():
    pass

def servidor_ativar_usuario():
    pass


def servidor_desativar_usuario():
    pass


@servidor_required
def servidor_cadastra_item(request):
    usuario = request.user
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    # Resolução da instituição ativa
    if cnpj_sessao:
        instituicao = usuario.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = usuario.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Você não possui vínculo ativo com nenhuma instituição parceira.")
        return redirect("login")

    if request.method == "POST":
        form = ServidorItemForm(request.POST, request.FILES, instituicao=instituicao)
        if form.is_valid():
            item = form.save(commit=False)
            item.instituicao = instituicao               # Garante o vínculo com a instituição ativa
            item.usuario_registro = usuario              # Servidor responsável pelo cadastro
            item.save()

            messages.success(
                request,
                f"Item '{item.nome or item.codigo}' cadastrado com sucesso! Código gerado: {item.codigo}"
            )
            return redirect("servidor_listar_itens")

        messages.error(request, "Por favor, corrija os erros apontados no formulário.")
    else:
        # Sugere por padrão o status ENCONTRADO (2) e a própria sala do servidor como local guardado
        dados_iniciais = {
            "status": Item.StatusItem.ENCONTRADO,
        }
        if usuario.sala and usuario.sala.instituicao == instituicao:
            dados_iniciais["local_guardado"] = usuario.sala

        form = ServidorItemForm(initial=dados_iniciais, instituicao=instituicao)

    context = {
        "form": form,
        "instituicao": instituicao,
    }
    return render(request, "serv/cadastrar_item.html", context)


@servidor_required
def servidor_detalhes_item(request, codigo):
    """
    Exibe os detalhes completos de um item da instituição ativa do servidor
    e lista todas as reivindicações registradas para este objeto (com filtro por status e paginação).
    """
    usuario = request.user
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    if cnpj_sessao:
        instituicao = usuario.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = usuario.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    # Busca o item garantindo que pertence à instituição do servidor
    item = get_object_or_404(
        Item.objects.select_related(
            "categoria",
            "local",
            "local_guardado",
            "usuario_registro",
            "dono",
        ),
        codigo=codigo,
        instituicao=instituicao,
    )

    # Lista todas as reivindicações vinculadas a este item
    reivindicacoes_qs = (
        Reivindicacao.objects.filter(item=item, instituicao=instituicao)
        .select_related("autor", "responsavel_admin", "local_devolucao")
        .order_by("-data")
    )

    # Filtro opcional por status da reivindicação
    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        reivindicacoes_qs = reivindicacoes_qs.filter(status=int(status_filtro))

    # Paginação das reivindicações (10 por página)
    paginator = Paginator(reivindicacoes_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "instituicao": instituicao,
        "item": item,
        "reivindicacoes": page_obj,
        "page_obj": page_obj,
        "status_filtro": status_filtro,
        "status_choices": Reivindicacao.StatusReivindicacao.choices,
        "total_reivindicacoes": paginator.count,
    }

    return render(request, "serv/detalhar_item.html", context)


@servidor_required
def servidor_detalhar_reivindicacao(request, protocolo):
    """
    Exibe todos os detalhes de uma reivindicação pelo protocolo, permitindo que o
    servidor analise, aprove, rejeite ou conclua a entrega do item.
    """
    usuario = request.user
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    if cnpj_sessao:
        instituicao = usuario.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = usuario.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    # Busca a reivindicação garantindo o vínculo institucional
    reivindicacao = get_object_or_404(
        Reivindicacao.objects.select_related(
            "autor",
            "item",
            "item__categoria",
            "item__local",
            "item__local_guardado",
            "responsavel_admin",
            "local_devolucao",
        ),
        protocolo=protocolo,
        instituicao=instituicao,
    )

    # Lista outras reivindicações concorrentes para o mesmo item (útil para comparação)
    outras_reivindicacoes = (
        Reivindicacao.objects.filter(
            item=reivindicacao.item,
            instituicao=instituicao,
        )
        .exclude(protocolo=reivindicacao.protocolo)
        .select_related("autor")
        .order_by("-data")
    )

    if request.method == "POST":
        form = ServidorAnaliseReivindicacaoForm(
            request.POST,
            instance=reivindicacao,
            instituicao=instituicao,
        )
        if form.is_valid():
            reiv_atualizada = form.save(commit=False)
            reiv_atualizada.responsavel_admin = usuario

            # Se marcada como CONCLUÍDA, registra data e atualiza o status do Item para DEVOLVIDO
            if reiv_atualizada.status == Reivindicacao.StatusReivindicacao.CONCLUIDA:
                agora = timezone.now()
                if not reiv_atualizada.data_devolucao:
                    reiv_atualizada.data_devolucao = agora

                item = reiv_atualizada.item
                item.status = Item.StatusItem.DEVOLVIDO
                item.dono = reiv_atualizada.autor
                item.data_devolucao = agora
                item.save(update_fields=["status", "dono", "data_devolucao"])

            reiv_atualizada.save()

            messages.success(
                request,
                f"Reivindicação #{reiv_atualizada.protocolo} atualizada para '{reiv_atualizada.get_status_display()}'.",
            )
            return redirect(
                "servidor_detalhar_reivindicacao",
                protocolo=reiv_atualizada.protocolo,
            )

        messages.error(request, "Verifique os erros apontados no formulário de análise.")
    else:
        # Sugere por padrão a sala onde o item está guardado caso ainda não haja local de devolução
        dados_iniciais = {}
        if not reivindicacao.local_devolucao and reivindicacao.item.local_guardado:
            dados_iniciais["local_devolucao"] = reivindicacao.item.local_guardado

        form = ServidorAnaliseReivindicacaoForm(
            instance=reivindicacao,
            initial=dados_iniciais,
            instituicao=instituicao,
        )

    context = {
        "instituicao": instituicao,
        "reivindicacao": reivindicacao,
        "item": reivindicacao.item,
        "outras_reivindicacoes": outras_reivindicacoes,
        "form": form,
    }

    return render(request, "serv/detalhar_reivindicacao.html", context)

def servidor_atualizar_item():
    pass


@servidor_required
def servidor_listar_reivindicacoes(request):
    """
    Lista todas as reivindicações da instituição vinculada ao servidor autenticado,
    ordenadas das mais recentes para as mais antigas, com suporte a:
    - Busca por protocolo, nome/código do item, nome/CPF/e-mail do solicitante ou descrição do pedido
    - Filtro por status da reivindicação
    - Filtro para exibir apenas reivindicações de itens cadastrados pelo próprio servidor
    - Paginação (12 itens por página)
    """
    usuario = request.user
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    if cnpj_sessao:
        instituicao = usuario.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = usuario.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Você não possui vínculo ativo com nenhuma instituição.")
        return redirect("servidor_painel")

    # Queryset base filtrado pela instituição do servidor e ordenado das mais recentes
    reivindicacoes_qs = (
        Reivindicacao.objects.filter(instituicao=instituicao)
        .select_related(
            "autor",
            "item",
            "item__categoria",
            "item__usuario_registro",
            "responsavel_admin",
            "local_devolucao",
        )
        .order_by("-data")
    )

    # 1. Pesquisa textual (Protocolo, Item, Solicitante ou Descrição do Pedido)
    termo_busca = request.GET.get("q", "").strip()
    if termo_busca:
        filtro_busca = (
            Q(item__nome__icontains=termo_busca)
            | Q(item__codigo__icontains=termo_busca)
            | Q(autor__nome__icontains=termo_busca)
            | Q(autor__email__icontains=termo_busca)
            | Q(autor__cpf__icontains=termo_busca)
            | Q(pedido__icontains=termo_busca)
        )
        protocolo_limpo = termo_busca.lstrip("#")
        if protocolo_limpo.isdigit():
            filtro_busca |= Q(protocolo=int(protocolo_limpo))

        reivindicacoes_qs = reivindicacoes_qs.filter(filtro_busca)

    # 2. Filtro por Status da Reivindicação
    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        reivindicacoes_qs = reivindicacoes_qs.filter(status=int(status_filtro))

    # 3. Filtro: Apenas itens cadastrados pelo servidor autenticado (?meus_itens=1)
    apenas_meus_itens = request.GET.get("meus_itens", "").strip() == "1"
    if apenas_meus_itens:
        reivindicacoes_qs = reivindicacoes_qs.filter(item__usuario_registro=usuario)

    # 4. Paginação (12 registros por página)
    paginator = Paginator(reivindicacoes_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "titulo": "Reivindicações da Unidade",
        "subtitulo": f"Solicitações de devolução registradas em {instituicao.nome}",
        "instituicao": instituicao,
        "reivindicacoes": page_obj,
        "page_obj": page_obj,
        "termo_busca": termo_busca,
        "status_filtro": status_filtro,
        "apenas_meus_itens": apenas_meus_itens,
        "status_choices": Reivindicacao.StatusReivindicacao.choices,
        "total_reivindicacoes": paginator.count,
    }

    return render(request, "serv/listar_reivindicacoes.html", context)