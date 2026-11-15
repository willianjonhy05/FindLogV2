from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q

from ..models import Item, Reivindicacao, Categoria

from ..decorators import usuario_required


@usuario_required
def usuario_feed(request):
    """
    Essa é a função principal que o usuário vai acessar assim que logar no sistema.
    Ela vai mostrar os itens encontrados na instituição a que ele está vinculado e
    que estão disponíveis para reivindicação, com suporte a pesquisa por nome.
    """
    usuario = request.user
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    if cnpj_sessao:
        instituicao = usuario.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = usuario.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Você não possui vínculo com nenhuma instituição ativa.")
        return redirect("login")

    itens = (
        Item.objects.filter(
            instituicao=instituicao,
            status=Item.StatusItem.ENCONTRADO,
        )
        .select_related("categoria", "local")
        .order_by("-data_registro")
    )

    # Pesquisa por nome do item
    termo_busca = request.GET.get("q", "").strip()
    if termo_busca:
        itens = itens.filter(nome__icontains=termo_busca)

    contexto = {
        "instituicao": instituicao,
        "itens": itens,
        "termo_busca": termo_busca,
    }

    return render(request, "usuario/feed.html", contexto)


@usuario_required
def usuario_feed_por_categoria(request, slug):
    """
    Exibe os itens encontrados na instituição vinculada ao usuário filtrados por
    uma categoria específica, mantendo a pesquisa por nome.
    """
    usuario = request.user
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    if cnpj_sessao:
        instituicao = usuario.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = usuario.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Você não possui vínculo com nenhuma instituição ativa.")
        return redirect("login")

    # Busca a categoria pelo slug garantindo que esteja ativa
    categoria = get_object_or_404(Categoria, slug=slug, ativa=True)

    # Filtra os itens disponíveis daquela instituição e categoria
    itens = (
        Item.objects.filter(
            instituicao=instituicao,
            categoria=categoria,
            status=Item.StatusItem.ENCONTRADO,
        )
        .select_related("categoria", "local")
        .order_by("-data_registro")
    )

    # Pesquisa por nome do item dentro da categoria selecionada
    termo_busca = request.GET.get("q", "").strip()
    if termo_busca:
        itens = itens.filter(nome__icontains=termo_busca)

    # Lista de categorias ativas para renderizar filtros/chips no feed
    categorias = Categoria.objects.filter(ativa=True).order_by("nome")

    contexto = {
        "instituicao": instituicao,
        "categoria_ativa": categoria,
        "categorias": categorias,
        "itens": itens,
        "termo_busca": termo_busca,
    }

    return render(request, "usuario/feed.html", contexto)


@usuario_required
def detalhar_item(request, uuid):
    """
    Exibe os detalhes de um item da instituição vinculada ao usuário
    e verifica se ele já possui uma reivindicação ativa para este objeto.
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
        return redirect("login")

    # Busca o item garantindo que pertence à mesma instituição do usuário
    item = get_object_or_404(
        Item.objects.select_related("categoria", "local"),
        instituicao=instituicao,
        uuid=uuid,
    )

    # Verifica se o usuário já abriu uma reivindicação para este item
    reivindicacao_existente = Reivindicacao.objects.filter(
        autor=usuario,
        item=item,
        instituicao=instituicao,
    ).first()

    context = {
        "instituicao": instituicao,
        "item": item,
        "reivindicacao_existente": reivindicacao_existente,
        "pode_reivindicar": (
            item.status == Item.StatusItem.ENCONTRADO and not reivindicacao_existente
        ),
    }

    return render(request, "usuario/item.html", context)


@usuario_required
def reivindicar_item(request, codigo_item):

    if request.method == "POST":

        with transaction.atomic():

            item = get_object_or_404(
                Item.objects.select_for_update(),
                codigo=codigo_item,
                instituicao__in=request.user.instituicao.filter(ativo=True),
            )

            if item.status != Item.StatusItem.ENCONTRADO:
                messages.error(request, "Este item não está disponível para reivindicação.")
                return redirect("usuario_feed")

            # Impede que o usuário reivindique um item associado à própria conta
            if item.usuario_registro == request.user or item.dono == request.user:
                messages.error(
                    request, "Você não pode reivindicar um item que já está associado à sua conta."
                )
                return redirect("usuario_feed")

            pedido = request.POST.get("pedido", "").strip()

            if not pedido:
                messages.error(
                    request, "Informe os motivos pelos quais você acredita que o item é seu."
                )
                return redirect("reivindicar_item", codigo_item=codigo_item)

            # Verifica se já existe uma reivindicação ativa
            status_ativos = [
                Reivindicacao.StatusReivindicacao.PENDENTE,
                Reivindicacao.StatusReivindicacao.EM_ANALISE,
                Reivindicacao.StatusReivindicacao.APROVADA,
            ]

            existe_reivindicacao = Reivindicacao.objects.filter(
                autor=request.user, item=item, status__in=status_ativos
            ).exists()

            if existe_reivindicacao:
                messages.warning(request, "Você já possui uma reivindicação para este item.")
                return redirect("minhas_reivindicacoes")

            Reivindicacao.objects.create(
                autor=request.user,
                item=item,
                instituicao=item.instituicao,
                pedido=pedido,
                anexos=request.FILES.get("anexos"),
            )

        messages.success(request, "Sua reivindicação foi enviada com sucesso!")
        return redirect("minhas_reivindicacoes")

    item = get_object_or_404(
        Item,
        codigo=codigo_item,
        instituicao__in=request.user.instituicao.filter(ativo=True),
        status=Item.StatusItem.ENCONTRADO,
    )

    # Também impede que o usuário acesse a página de reivindicação
    # de um item associado à própria conta
    if item.usuario_registro == request.user or item.dono == request.user:
        messages.error(
            request, "Você não pode reivindicar um item que já está associado à sua conta."
        )
        return redirect("usuario_feed")

    return render(request, "usuario/reivindicar_item.html", {"item": item})


@login_required
def meu_perfil(request):
    """
    Essa é a função que o usuário vai acessar para ver as informações do seu perfil.
    """

    usuario = request.user

    reivindicacoes = Reivindicacao.objects.filter(autor=usuario)

    contexto = {
        "usuario": usuario,
        "quantidade_reivindicacoes": reivindicacoes.count(),
        "reivindicacoes_pendentes": reivindicacoes.filter(
            status=Reivindicacao.StatusReivindicacao.PENDENTE
        ).count(),
        "reivindicacoes_aprovadas": reivindicacoes.filter(
            status=Reivindicacao.StatusReivindicacao.APROVADA
        ).count(),
        "instituicoes": usuario.instituicao.filter(ativo=True),
    }

    return render(request, "usuario/meu_perfil.html", contexto)


@login_required
def editar_meu_perfil(request):
    """
    Essa é a função que o usuário vai acessar para editar as informações do seu perfil.
    """

    usuario = request.user

    if request.method == "POST":

        nome = request.POST.get("nome", "").strip()
        email = request.POST.get("email", "").strip()
        telefone = request.POST.get("telefone", "").strip()

        data_nascimento_texto = request.POST.get("data_nascimento", "").strip()

        data_nascimento = parse_date(data_nascimento_texto) if data_nascimento_texto else None

        if not nome or not email:

            messages.error(request, "Nome e e-mail são obrigatórios.")

        elif data_nascimento_texto and not data_nascimento:

            messages.error(request, "Informe uma data de nascimento válida.")

        elif usuario.__class__.objects.filter(email__iexact=email).exclude(pk=usuario.pk).exists():

            messages.error(request, "Este e-mail já está cadastrado.")

        else:

            usuario.nome = nome
            usuario.email = email
            usuario.telefone = telefone
            usuario.data_nascimento = data_nascimento

            if request.FILES.get("foto"):
                usuario.foto = request.FILES["foto"]

            usuario.save()

            messages.success(request, "Seu perfil foi atualizado com sucesso!")

            return redirect("meu_perfil")

    contexto = {"usuario": usuario}

    return render(request, "usuario/editar_perfil.html", contexto)


@login_required
def trocar_senha(request):
    """
    Função para o usuário trocar a senha de acesso ao sistema.
    """

    if request.method == "POST":

        form = PasswordChangeForm(user=request.user, data=request.POST)

        if form.is_valid():

            usuario = form.save()

            update_session_auth_hash(request, usuario)

            messages.success(request, "Sua senha foi alterada com sucesso!")

            return redirect("meu_perfil")

        else:

            messages.error(request, "Verifique os dados informados e tente novamente.")

    else:

        form = PasswordChangeForm(user=request.user)

    return render(request, "usuario/trocar_senha.html", {"form": form})


def minhas_reivindicacoes(request):
    """
    Exibe as reivindicações feitas pelo usuário autenticado na instituição ativa,
    com suporte a busca por nome do item ou protocolo, filtro de status e paginação.
    """
    usuario = request.user
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    if cnpj_sessao:
        instituicao = usuario.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = usuario.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Você não possui vínculo com nenhuma instituição ativa.")
        return redirect("login")

    # Queryset base ordenado das mais recentes para as mais antigas
    reivindicacoes_qs = (
        Reivindicacao.objects.filter(autor=usuario, instituicao=instituicao)
        .select_related("item", "item__categoria", "local_devolucao")
        .order_by("-data")
    )

    # 1. Pesquisa por nome do item ou número de protocolo
    termo_busca = request.GET.get("q", "").strip()
    if termo_busca:
        filtro_busca = Q(item__nome__icontains=termo_busca)
        protocolo_limpo = termo_busca.lstrip("#")
        if protocolo_limpo.isdigit():
            filtro_busca |= Q(protocolo=int(protocolo_limpo))
        reivindicacoes_qs = reivindicacoes_qs.filter(filtro_busca)

    # 2. Filtro por status da reivindicação
    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        reivindicacoes_qs = reivindicacoes_qs.filter(status=int(status_filtro))

    # 3. Paginação (10 itens por página)
    paginator = Paginator(reivindicacoes_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    contexto = {
        "instituicao": instituicao,
        "reivindicacoes": page_obj,
        "page_obj": page_obj,
        "termo_busca": termo_busca,
        "status_filtro": status_filtro,
        "status_choices": Reivindicacao.StatusReivindicacao.choices,
        "total_reivindicacoes": paginator.count,
    }

    return render(request, "usuario/minhas_reivindicacoes.html", contexto)
