from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db import transaction

from .models import Item, Reivindicacao, Categoria, Instituicao

@login_required
def usuario_feed(request):
    """"
    Essa é a função principal que o usuário vai acessar assim que logar no sistema. 
    Ela vai mostrar os itens, encontrados na instituição que ela é vinculada e
    que estão disponíveis para reivindicação.
    """
    
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.get(cnpj=cnpj_sessao)

    if not instituicao:
        messages.error(request, "Você não possui vínculo com nenhuma instituição ativa.")
        return redirect("login")

    itens = Item.objects.filter(instituicao=instituicao).order_by("-data_registro")

    contexto = {
        'itens': itens,
    }

    return render(request, 'usuario/feed.html', contexto)



def detalhar_item(request, uuid):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = Instituicao.objects.get(cnpj=cnpj_sessao)

    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect('servidor_painel')

    item = get_object_or_404(Item, instituicao=instituicao, uuid=uuid)

    context = {
        "item": item
    }    

    return render(request, "usuario/item.html", context)

@login_required
def reivindicar_item(request, codigo_item):

    if request.method == 'POST':

        with transaction.atomic():

            item = get_object_or_404(
                Item.objects.select_for_update(),
                codigo=codigo_item,
                instituicao__in=request.user.instituicao.filter(ativo=True)
            )

            if item.status != Item.StatusItem.ENCONTRADO:
                messages.error(
                    request,
                    'Este item não está disponível para reivindicação.'
                )
                return redirect('usuario_feed')

            # Impede que o usuário reivindique um item associado à própria conta
            if item.usuario_registro == request.user or item.dono == request.user:
                messages.error(
                    request,
                    'Você não pode reivindicar um item que já está associado à sua conta.'
                )
                return redirect('usuario_feed')

            pedido = request.POST.get('pedido', '').strip()

            if not pedido:
                messages.error(
                    request,
                    'Informe os motivos pelos quais você acredita que o item é seu.'
                )
                return redirect(
                    'reivindicar_item',
                    codigo_item=codigo_item
                )

            # Verifica se já existe uma reivindicação ativa
            status_ativos = [
                Reivindicacao.StatusReivindicacao.PENDENTE,
                Reivindicacao.StatusReivindicacao.EM_ANALISE,
                Reivindicacao.StatusReivindicacao.APROVADA,
            ]

            existe_reivindicacao = Reivindicacao.objects.filter(
                autor=request.user,
                item=item,
                status__in=status_ativos
            ).exists()

            if existe_reivindicacao:
                messages.warning(
                    request,
                    'Você já possui uma reivindicação para este item.'
                )
                return redirect('minhas_reivindicacoes')

            Reivindicacao.objects.create(
                autor=request.user,
                item=item,
                instituicao=item.instituicao,
                pedido=pedido,
                anexos=request.FILES.get('anexos')
            )

        messages.success(
            request,
            'Sua reivindicação foi enviada com sucesso!'
        )
        return redirect('minhas_reivindicacoes')

    item = get_object_or_404(
        Item,
        codigo=codigo_item,
        instituicao__in=request.user.instituicao.filter(ativo=True),
        status=Item.StatusItem.ENCONTRADO
    )

    # Também impede que o usuário acesse a página de reivindicação
    # de um item associado à própria conta
    if item.usuario_registro == request.user or item.dono == request.user:
        messages.error(
            request,
            'Você não pode reivindicar um item que já está associado à sua conta.'
        )
        return redirect('usuario_feed')

    return render(
        request,
        'usuario/reivindicar_item.html',
        {'item': item}
    )


@login_required
def itens_por_categoria(request, categoria):
    """
    Essa é a função que o usuário vai acessar para mostrar os itens, 
    encontrados na instituição que ele é vinculado de determinada categoria
    que estão disponíveis para reivindicação.
    """

    instituicoes = request.user.instituicao.filter(ativo=True)

    categoria_obj = get_object_or_404(
        Categoria,
        slug=categoria,
        ativa=True
    )

    itens = Item.objects.filter(
        instituicao__in=instituicoes,
        categoria=categoria_obj,
        status=Item.StatusItem.ENCONTRADO
    ).select_related(
        'categoria',
        'instituicao',
        'local'
    ).order_by('-data_registro')

    contexto = {
        'itens': itens,
        'categoria_atual': categoria_obj,
        'quantidade': itens.count()
    }

    return render(
        request,
        'usuario/categoria.html',
        contexto
    )

@login_required
def meu_perfil(request):
    """
    Essa é a função que o usuário vai acessar para ver as informações do seu perfil.
    """

    usuario = request.user

    reivindicacoes = Reivindicacao.objects.filter(
        autor=usuario
    )

    contexto = {
        'usuario': usuario,

        'quantidade_reivindicacoes': reivindicacoes.count(),

        'reivindicacoes_pendentes': reivindicacoes.filter(
            status=Reivindicacao.StatusReivindicacao.PENDENTE
        ).count(),

        'reivindicacoes_aprovadas': reivindicacoes.filter(
            status=Reivindicacao.StatusReivindicacao.APROVADA
        ).count(),

        'instituicoes': usuario.instituicao.filter(ativo=True),
    }

    return render(
        request,
        'usuario/meu_perfil.html',
        contexto
    )

@login_required
def editar_meu_perfil(request):
    """
    Essa é a função que o usuário vai acessar para editar as informações do seu perfil.
    """

    usuario = request.user

    if request.method == 'POST':

        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        telefone = request.POST.get('telefone', '').strip()

        data_nascimento_texto = request.POST.get(
            'data_nascimento', ''
        ).strip()

        data_nascimento = (
            parse_date(data_nascimento_texto)
            if data_nascimento_texto else None
        )

        if not nome or not email:

            messages.error(
                request,
                'Nome e e-mail são obrigatórios.'
            )

        elif data_nascimento_texto and not data_nascimento:

            messages.error(
                request,
                'Informe uma data de nascimento válida.'
            )

        elif usuario.__class__.objects.filter(
            email__iexact=email
        ).exclude(pk=usuario.pk).exists():

            messages.error(
                request,
                'Este e-mail já está cadastrado.'
            )

        else:

            usuario.nome = nome
            usuario.email = email
            usuario.telefone = telefone
            usuario.data_nascimento = data_nascimento

            if request.FILES.get('foto'):
                usuario.foto = request.FILES['foto']

            usuario.save()

            messages.success(
                request,
                'Seu perfil foi atualizado com sucesso!'
            )

            return redirect('meu_perfil')

    contexto = {
        'usuario': usuario
    }

    return render(
        request,
        'usuario/editar_perfil.html',
        contexto
    )

@login_required
def trocar_senha(request):
    """
    Função para o usuário trocar a senha de acesso ao sistema.
    """

    if request.method == 'POST':

        form = PasswordChangeForm(
            user=request.user,
            data=request.POST
        )

        if form.is_valid():

            usuario = form.save()

            update_session_auth_hash(request, usuario)

            messages.success(
                request,
                'Sua senha foi alterada com sucesso!'
            )

            return redirect('meu_perfil')

        else:

            messages.error(
                request,
                'Verifique os dados informados e tente novamente.'
            )

    else:

        form = PasswordChangeForm(user=request.user)

    return render(
        request,
        'usuario/trocar_senha.html',
        {'form': form}
    )

@login_required
def minhas_reivindicacoes(request):
    """"
    Essa é a função que o usuário vai acessar para ver as reivindicações que ele fez. 
    """     

    reivindicacoes = Reivindicacao.objects.filter(
        autor=request.user
    ).select_related(
        'item',
        'instituicao',
        'responsavel_admin'
    ).order_by('-data')

    contexto = {
        'reivindicacoes': reivindicacoes,
        'quantidade': reivindicacoes.count()
    }

    return render(
        request,
        'usuario/minhas_reivindicacoes.html',
        contexto
    )






