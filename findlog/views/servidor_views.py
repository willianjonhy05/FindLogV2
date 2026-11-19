from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..decorators import servidor_required
from ..forms.item import ServidorAtualizarItemForm, ServidorItemForm
from ..forms.perfil import (
    ServidorAlterarSenhaForm,
    ServidorCadastroColegaForm,
    ServidorEditarUserForm,
)
from ..forms.reivindicacao import ServidorAnaliseReivindicacaoForm
from ..forms.sala import ServidorSalaForm, ServidorUpdateSalaForm
from ..models import Categoria, Item, Perfil, Reivindicacao, Sala
from ..utils import (
    _obter_instituicao_servidor,
    _obter_perfil_servidor,
    apenas_digitos,
    gerar_qrcode_base64,
    redirecionar_origem,
    _paginar_queryset
)


# ==============================================================================
# HELPERS INTERNOS DA ÁREA DO SERVIDOR
# ==============================================================================


def _obter_instituicao_ativa(request):
    """Retorna a instituição ativa da sessão ou o primeiro vínculo ativo do usuário."""
    return _obter_instituicao_servidor(request)


def _obter_perfil_da_instituicao(instituicao, username):
    """
    Busca um usuário comum ou servidor pelo username vinculado à instituição informada,
    bloqueando o acesso a superusuários e administradores da plataforma.
    """
    return get_object_or_404(
        Perfil.objects.select_related("sala"),
        username=username,
        instituicao=instituicao,
        is_superuser=False,
        tipo__in=[Perfil.TipoUsuario.USUARIO, Perfil.TipoUsuario.SERVIDOR],
    )


# ==============================================================================
# 1. DASHBOARD / PAINEL DO SERVIDOR
# ==============================================================================


@servidor_required
def servidor_painel(request):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Você não possui vínculo com nenhuma instituição ativa.")
        return redirect("login")

    # Contagens métricas para os cards do dashboard
    qtde_reivindicacoes = Reivindicacao.objects.filter(instituicao=instituicao).count()
    qtde_itens = Item.objects.filter(instituicao=instituicao).count()
    qtde_salas = Sala.objects.filter(instituicao=instituicao).count()

    contagem_perfis = Perfil.objects.filter(instituicao=instituicao).aggregate(
        usuarios=Count("id", filter=Q(tipo=Perfil.TipoUsuario.USUARIO), distinct=True),
        servidores=Count("id", filter=Q(tipo=Perfil.TipoUsuario.SERVIDOR), distinct=True),
    )

    # Últimos itens registrados para exibição rápida no painel
    ultimos_itens = (
        Item.objects.filter(instituicao=instituicao)
        .select_related("categoria", "local")
        .order_by("-data_registro")[:5]
    )

    # Links absolutos e QR Codes em Base64 para convites de autocadastro
    token = instituicao.token_convite
    link_convite_usuario = request.build_absolute_uri(
        reverse("novo_usuario_instituicao", kwargs={"token": token})
    )
    link_convite_servidor = request.build_absolute_uri(
        reverse("novo_servidor_instituicao", kwargs={"token": token})
    )

    context = {
        "instituicao": instituicao,
        "qtde_reivindicacoes": qtde_reivindicacoes,
        "qtde_itens": qtde_itens,
        "qtde_usuarios": contagem_perfis["usuarios"],
        "qtde_servidores": contagem_perfis["servidores"],
        "qtde_salas": qtde_salas,
        "ultimos_itens": ultimos_itens,
        "link_convite_usuario": link_convite_usuario,
        "link_convite_servidor": link_convite_servidor,
        "qrcode_usuario": gerar_qrcode_base64(link_convite_usuario),
        "qrcode_servidor": gerar_qrcode_base64(link_convite_servidor),
    }
    return render(request, "serv/index.html", context)


# ==============================================================================
# 2. GESTÃO DE SALAS E AMBIENTES
# ==============================================================================


@servidor_required
def servidor_listar_salas(request):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Você não possui vínculo ativo com nenhuma instituição parceira.")
        return redirect("login")

    salas_qs = Sala.objects.filter(instituicao=instituicao).order_by("predio", "andar", "nome")

    termo_busca = request.GET.get("q", "").strip()
    if termo_busca:
        salas_qs = salas_qs.filter(
            Q(nome__icontains=termo_busca)
            | Q(predio__icontains=termo_busca)
            | Q(codigo__icontains=termo_busca)
            | Q(andar__icontains=termo_busca)
        )

    page_obj, total_salas = _paginar_queryset(request, salas_qs, por_pagina=9)

    context = {
        "instituicao": instituicao,
        "page_obj": page_obj,
        "termo_busca": termo_busca,
        "total_salas": total_salas,
    }
    return render(request, "serv/salas.html", context)


@servidor_required
def servidor_cadastrar_sala(request):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Você não possui vínculo ativo com nenhuma instituição parceira.")
        return redirect("servidor_painel")

    if request.method == "POST":
        form = ServidorSalaForm(request.POST)
        if form.is_valid():
            sala = form.save(commit=False)
            sala.instituicao = instituicao
            sala.ativa = True
            sala.save()

            messages.success(
                request,
                f"Sala '{sala.nome}' cadastrada com sucesso na unidade {instituicao.nome}!",
            )
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
def servidor_detalhar_sala(request, codigo):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)
    return render(request, "serv/detalhar_sala.html", {"sala": sala})


@servidor_required
def servidor_editar_sala(request, codigo):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Vínculo institucional não encontrado para este usuário.")
        return redirect("servidor_painel")

    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)

    if request.method == "POST":
        form = ServidorUpdateSalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            messages.success(request, f'Sala "{sala.nome}" atualizada com sucesso!')
            return redirect("servidor_listar_salas")
    else:
        form = ServidorUpdateSalaForm(instance=sala)

    context = {
        "form": form,
        "sala": sala,
        "instituicao": instituicao,
    }
    return render(request, "serv/editar_sala.html", context)


@servidor_required
@require_POST
def servidor_alternar_status_sala(request, codigo):
    """Alterna o status da sala (ativa/inativa) via POST e retorna para a página de origem."""
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)
    sala.ativa = not sala.ativa
    sala.save(update_fields=["ativa"])

    status_str = "ativada" if sala.ativa else "desativada"
    messages.success(request, f"A sala '{sala.nome}' foi {status_str} com sucesso.")
    return redirecionar_origem(request, fallback="servidor_listar_salas")


@servidor_required
@require_POST
def servidor_ativar_sala(request, codigo):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)

    if not sala.ativa:
        sala.ativa = True
        sala.save(update_fields=["ativa"])
        messages.success(request, f'A sala "{sala.nome}" foi reativada com sucesso.')
    else:
        messages.info(request, f'A sala "{sala.nome}" já se encontra ativa.')

    return redirecionar_origem(request, fallback="servidor_listar_salas")


@servidor_required
@require_POST
def servidor_desativar_sala(request, codigo):
    instituicao = _obter_instituicao_ativa(request)
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

    return redirecionar_origem(request, fallback="servidor_detalhar_sala", codigo=sala.codigo)


@servidor_required
@require_POST
def servidor_excluir_sala(request, codigo):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)
    nome_sala = sala.nome
    sala.delete()

    messages.success(request, f'A sala "{nome_sala}" foi excluída permanentemente.')
    return redirect("servidor_listar_salas")


# ==============================================================================
# 3. GESTÃO DE ITENS ACHADOS E PERDIDOS
# ==============================================================================


@servidor_required
def servidor_listar_itens(request):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    itens_qs = (
        Item.objects.filter(instituicao=instituicao)
        .select_related("categoria", "local", "local_guardado", "usuario_registro")
        .order_by("-data_registro")
    )

    q = request.GET.get("q", "").strip()
    if q:
        itens_qs = itens_qs.filter(
            Q(nome__icontains=q)
            | Q(codigo__icontains=q)
            | Q(descricao__icontains=q)
            | Q(marca_ou_modelo__icontains=q)
            | Q(cor__icontains=q)
        )

    categoria_filtro = request.GET.get("categoria", "").strip()
    if categoria_filtro:
        itens_qs = itens_qs.filter(categoria_id=categoria_filtro)

    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        itens_qs = itens_qs.filter(status=int(status_filtro))

    apenas_meus_itens = request.GET.get("meus_itens", "").strip() == "1"
    if apenas_meus_itens:
        itens_qs = itens_qs.filter(usuario_registro=request.user)

    page_obj, total_itens = _paginar_queryset(request, itens_qs, por_pagina=9)
    categorias = Categoria.objects.filter(ativa=True).order_by("nome")

    context = {
        "titulo": "Todos os Itens Registrados",
        "subtitulo": f"Itens achados e perdidos da unidade: {instituicao.nome}",
        "instituicao": instituicao,
        "page_obj": page_obj,
        "termo_busca": q,
        "categoria_filtro": categoria_filtro,
        "categorias": categorias,
        "status_filtro": status_filtro,
        "apenas_meus_itens": apenas_meus_itens,
        "status_choices": Item.StatusItem.choices,
        "total_itens": total_itens,
    }
    return render(request, "serv/listar_itens.html", context)


@servidor_required
def servidor_itens_por_sala(request, sala_codigo):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    sala = get_object_or_404(Sala, codigo=sala_codigo, instituicao=instituicao)

    itens_qs = (
        Item.objects.filter(Q(instituicao=instituicao) & (Q(local=sala) | Q(local_guardado=sala)))
        .select_related("categoria", "local", "local_guardado")
        .order_by("-data_registro")
    )

    q = request.GET.get("q", "").strip()
    if q:
        itens_qs = itens_qs.filter(
            Q(nome__icontains=q) | Q(codigo__icontains=q) | Q(marca_ou_modelo__icontains=q)
        )

    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        itens_qs = itens_qs.filter(status=int(status_filtro))

    page_obj, total_itens = _paginar_queryset(request, itens_qs, por_pagina=12)

    context = {
        "titulo": f"Itens na Sala: {sala.nome}",
        "subtitulo": f"Prédio {sala.predio}, Andar {sala.andar} - {instituicao.nome}",
        "instituicao": instituicao,
        "sala": sala,
        "page_obj": page_obj,
        "termo_busca": q,
        "status_filtro": status_filtro,
        "status_choices": Item.StatusItem.choices,
        "total_itens": total_itens,
    }
    return render(request, "serv/listar_itens.html", context)


@servidor_required
def servidor_itens_por_categoria(request, categoria_id):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    categoria = get_object_or_404(Categoria, pk=categoria_id)

    itens_qs = (
        Item.objects.filter(instituicao=instituicao, categoria=categoria)
        .select_related("categoria", "local", "local_guardado")
        .order_by("-data_registro")
    )

    q = request.GET.get("q", "").strip()
    if q:
        itens_qs = itens_qs.filter(
            Q(nome__icontains=q) | Q(codigo__icontains=q) | Q(marca_ou_modelo__icontains=q)
        )

    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        itens_qs = itens_qs.filter(status=int(status_filtro))

    page_obj, total_itens = _paginar_queryset(request, itens_qs, por_pagina=12)

    context = {
        "titulo": f"Categoria: {categoria.nome}",
        "subtitulo": f"Itens classificados como '{categoria.nome}' em {instituicao.nome}",
        "instituicao": instituicao,
        "categoria": categoria,
        "page_obj": page_obj,
        "termo_busca": q,
        "status_filtro": status_filtro,
        "status_choices": Item.StatusItem.choices,
        "total_itens": total_itens,
    }
    return render(request, "serv/listar_itens.html", context)


@servidor_required
def servidor_cadastra_item(request):
    usuario = request.user
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Você não possui vínculo ativo com nenhuma instituição parceira.")
        return redirect("login")

    if request.method == "POST":
        form = ServidorItemForm(
            request.POST,
            request.FILES,
            instituicao=instituicao,
            user=usuario,
        )
        if form.is_valid():
            item = form.save(commit=False)
            item.instituicao = instituicao
            item.usuario_registro = usuario
            item.save()

            messages.success(
                request,
                f"Item '{item.nome or item.codigo}' cadastrado com sucesso! Código gerado: {item.codigo}",
            )
            return redirect("servidor_listar_itens")

        messages.error(request, "Por favor, corrija os erros apontados no formulário.")
    else:
        dados_iniciais = {"status": Item.StatusItem.ENCONTRADO}
        if usuario.sala and usuario.sala.instituicao == instituicao and usuario.sala.ativa:
            dados_iniciais["local_guardado"] = ServidorItemForm._formatar_rotulo_sala(usuario.sala)

        form = ServidorItemForm(
            initial=dados_iniciais,
            instituicao=instituicao,
            user=usuario,
        )

    context = {
        "form": form,
        "instituicao": instituicao,
    }
    return render(request, "serv/cadastrar_item.html", context)


@servidor_required
def servidor_detalhes_item(request, uuid):
    """
    Exibe os detalhes completos de um item da instituição ativa do servidor
    e lista todas as reivindicações registradas para este objeto.
    """
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    item = get_object_or_404(
        Item.objects.select_related(
            "categoria",
            "local",
            "local_guardado",
            "usuario_registro",
            "dono",
        ),
        uuid=uuid,
        instituicao=instituicao,
    )

    reivindicacoes_qs = (
        Reivindicacao.objects.filter(item=item, instituicao=instituicao)
        .select_related("autor", "responsavel_admin", "local_devolucao")
        .order_by("-data")
    )

    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit() and int(status_filtro) in Reivindicacao.StatusReivindicacao.values:
        reivindicacoes_qs = reivindicacoes_qs.filter(status=int(status_filtro))

    page_obj, total_reivindicacoes = _paginar_queryset(request, reivindicacoes_qs, por_pagina=10)

    context = {
        "instituicao": instituicao,
        "item": item,
        "reivindicacoes": page_obj,
        "page_obj": page_obj,
        "status_filtro": status_filtro,
        "status_choices": Reivindicacao.StatusReivindicacao.choices,
        "total_reivindicacoes": total_reivindicacoes,
    }
    return render(request, "serv/detalhar_item.html", context)


@servidor_required
def servidor_atualizar_item(request, uuid):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    item = get_object_or_404(
        Item.objects.select_related("categoria", "local", "local_guardado", "dono"),
        uuid=uuid,
        instituicao=instituicao,
    )

    if request.method == "POST":
        form = ServidorAtualizarItemForm(
            request.POST,
            request.FILES,
            instance=item,
            instituicao=instituicao,
            user=request.user,
        )
        if form.is_valid():
            item_atualizado = form.save()
            messages.success(
                request,
                f'Os dados do item "{item_atualizado.nome or item_atualizado.codigo}" foram atualizados com sucesso.',
            )
            return redirect("servidor_detalhes_item", uuid=item_atualizado.uuid)

        messages.error(request, "Verifique os erros no formulário antes de salvar.")
    else:
        form = ServidorAtualizarItemForm(
            instance=item,
            instituicao=instituicao,
            user=request.user,
        )

    context = {
        "form": form,
        "item": item,
        "instituicao": instituicao,
    }
    return render(request, "serv/atualizar_item.html", context)


@servidor_required
@require_POST
def servidor_apagar_item(request, uuid):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    item = get_object_or_404(Item, uuid=uuid, instituicao=instituicao)

    if item.status == Item.StatusItem.DEVOLVIDO:
        messages.warning(request, "Não é possível apagar um item que já foi devolvido.")
        return redirect("servidor_detalhes_item", uuid=item.uuid)

    nome_item = item.nome or item.codigo
    item.delete()

    messages.success(request, f'O item "{nome_item}" foi removido com sucesso.')
    return redirect("servidor_listar_itens")


# ==============================================================================
# 4. GESTÃO DE USUÁRIOS & EQUIPE DA UNIDADE
# ==============================================================================


@servidor_required
def servidor_cadastrar_usuario(request):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Você não está vinculado a nenhuma instituição ativa.")
        return redirect("login")

    if request.method == "POST":
        dados_post = request.POST.copy()

        if dados_post.get("cpf"):
            dados_post["cpf"] = apenas_digitos(dados_post["cpf"])
        if dados_post.get("telefone"):
            dados_post["telefone"] = apenas_digitos(dados_post["telefone"])

        form = ServidorCadastroColegaForm(dados_post, instituicao=instituicao)

        if form.is_valid():
            novo_usuario = form.save()
            tipo_label = novo_usuario.get_tipo_display()
            messages.success(
                request,
                f"{tipo_label} '{novo_usuario.nome or novo_usuario.username}' cadastrado(a) com sucesso!",
            )
            return redirect("servidor_usuarios_instituicao")

        messages.error(request, "Verifique os erros nos campos antes de continuar.")
    else:
        form = ServidorCadastroColegaForm(instituicao=instituicao)

    context = {
        "form": form,
        "instituicao": instituicao,
    }
    return render(request, "serv/cadastrar_usuario.html", context)


@servidor_required
def servidor_usuarios_instituicao(request):
    """Lista paginada de todos os usuários e servidores vinculados à instituição ativa."""
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    tipos_permitidos = [
        (Perfil.TipoUsuario.USUARIO, "Usuário"),
        (Perfil.TipoUsuario.SERVIDOR, "Servidor"),
    ]

    perfis_qs = (
        Perfil.objects.filter(
            instituicao=instituicao,
            is_superuser=False,
            tipo__in=[Perfil.TipoUsuario.USUARIO, Perfil.TipoUsuario.SERVIDOR],
        )
        .select_related("sala")
        .distinct()
        .order_by("ativo", "-criado_em")
    )

    q = request.GET.get("q", "").strip()
    if q:
        q_digitos = apenas_digitos(q)
        filtro_busca = (
            Q(nome__icontains=q)
            | Q(email__icontains=q)
            | Q(username__icontains=q)
            | Q(codigo__icontains=q)
        )
        if q_digitos:
            filtro_busca |= Q(cpf__icontains=q_digitos) | Q(telefone__icontains=q_digitos)

        perfis_qs = perfis_qs.filter(filtro_busca)

    tipo_filtro = request.GET.get("tipo", "").strip()
    if tipo_filtro.isdigit() and int(tipo_filtro) in [
        Perfil.TipoUsuario.USUARIO,
        Perfil.TipoUsuario.SERVIDOR,
    ]:
        perfis_qs = perfis_qs.filter(tipo=int(tipo_filtro))

    status_filtro = request.GET.get("status", "").strip()
    if status_filtro == "ativo":
        perfis_qs = perfis_qs.filter(ativo=True)
    elif status_filtro == "inativo":
        perfis_qs = perfis_qs.filter(ativo=False)

    page_obj, total_perfis = _paginar_queryset(request, perfis_qs, por_pagina=12)

    context = {
        "titulo": "Usuários & Equipe da Unidade",
        "subtitulo": f"Perfis vinculados à instituição: {instituicao.nome}",
        "instituicao": instituicao,
        "page_obj": page_obj,
        "termo_busca": q,
        "tipo_filtro": tipo_filtro,
        "status_filtro": status_filtro,
        "tipos_choices": tipos_permitidos,
        "total_perfis": total_perfis,
    }
    return render(request, "serv/usuarios_instituicao.html", context)


@servidor_required
def servidor_visualizar_usuario(request, username):
    """Exibe os detalhes cadastrais e o histórico institucional de um usuário ou servidor."""
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    perfil = _obter_perfil_da_instituicao(instituicao, username)

    reivindicacoes = (
        Reivindicacao.objects.filter(autor=perfil, instituicao=instituicao)
        .select_related("item")
        .order_by("-data")[:10]
    )

    itens_registrados = (
        Item.objects.filter(usuario_registro=perfil, instituicao=instituicao)
        .select_related("categoria", "local")
        .order_by("-data_registro")[:10]
    )

    context = {
        "titulo": "Detalhes do Perfil",
        "subtitulo": f"Visualização de vínculo na unidade: {instituicao.nome}",
        "instituicao": instituicao,
        "perfil": perfil,
        "reivindicacoes": reivindicacoes,
        "itens_registrados": itens_registrados,
    }
    return render(request, "serv/visualizar_usuario.html", context)


@servidor_required
@require_POST
def servidor_ativar_usuario(request, username):
    """Ativa o acesso de um usuário ou aprova o cadastro pendente de um servidor."""
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    perfil = _obter_perfil_da_instituicao(instituicao, username)

    if perfil.pk == request.user.pk:
        messages.warning(request, "Você não pode alterar o status do seu próprio perfil.")
        return redirect("servidor_usuarios_instituicao")

    if perfil.ativo:
        messages.info(request, f"O perfil de {perfil.nome or perfil.username} já está ativo.")
    else:
        perfil.ativo = True
        perfil.is_active = True
        perfil.save(update_fields=["ativo", "is_active"])
        papel = "Servidor" if perfil.tipo == Perfil.TipoUsuario.SERVIDOR else "Usuário"
        messages.success(
            request,
            f"{papel} {perfil.nome or perfil.username} ativado(a) com sucesso!",
        )

    return redirecionar_origem(request, fallback="servidor_usuarios_instituicao")


@servidor_required
@require_POST
def servidor_desativar_usuario(request, username):
    """Bloqueia temporariamente o acesso de um usuário ou servidor da unidade."""
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    perfil = _obter_perfil_da_instituicao(instituicao, username)

    if perfil.pk == request.user.pk:
        messages.error(request, "Operação bloqueada: você não pode desativar sua própria conta.")
        return redirect("servidor_usuarios_instituicao")

    if not perfil.ativo:
        messages.info(
            request, f"O perfil de {perfil.nome or perfil.username} já encontra-se desativado."
        )
    else:
        perfil.ativo = False
        perfil.is_active = False
        perfil.save(update_fields=["ativo", "is_active"])
        papel = "Servidor" if perfil.tipo == Perfil.TipoUsuario.SERVIDOR else "Usuário"
        messages.warning(
            request,
            f"O acesso de {papel.lower()} {perfil.nome or perfil.username} foi desativado.",
        )

    return redirecionar_origem(request, fallback="servidor_usuarios_instituicao")


# ==============================================================================
# 5. ANÁLISE E LISTAGEM DE REIVINDICAÇÕES
# ==============================================================================


@servidor_required
def servidor_listar_reivindicacoes(request):
    """
    Exibe por padrão as reivindicações de itens cadastrados pelo servidor logado,
    permitindo alternar para todas as reivindicações da unidade.
    """
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Você não possui vínculo ativo com nenhuma instituição.")
        return redirect("servidor_painel")

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

    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        reivindicacoes_qs = reivindicacoes_qs.filter(status=int(status_filtro))

    meus_itens_param = request.GET.get("meus_itens", "").strip()
    foi_filtrado = request.GET.get("filtrar", "").strip() == "1"

    if meus_itens_param == "0":
        apenas_meus_itens = False
    elif foi_filtrado:
        apenas_meus_itens = meus_itens_param == "1"
    else:
        apenas_meus_itens = True

    if apenas_meus_itens:
        reivindicacoes_qs = reivindicacoes_qs.filter(item__usuario_registro=request.user)

    page_obj, total_reivindicacoes = _paginar_queryset(request, reivindicacoes_qs, por_pagina=12)

    context = {
        "titulo": (
            "Reivindicações dos Meus Itens" if apenas_meus_itens else "Reivindicações da Unidade"
        ),
        "subtitulo": f"Solicitações de devolução registradas em {instituicao.nome}",
        "instituicao": instituicao,
        "reivindicacoes": page_obj,
        "page_obj": page_obj,
        "termo_busca": termo_busca,
        "status_filtro": status_filtro,
        "apenas_meus_itens": apenas_meus_itens,
        "status_choices": Reivindicacao.StatusReivindicacao.choices,
        "total_reivindicacoes": total_reivindicacoes,
    }
    return render(request, "serv/listar_reivindicacoes.html", context)


@servidor_required
def servidor_detalhar_reivindicacao(request, protocolo):
    """
    Exibe todos os detalhes de uma reivindicação pelo protocolo, permitindo que o
    servidor analise, aprove, rejeite ou conclua a entrega do item.
    """
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

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
            with transaction.atomic():
                reiv_atualizada = form.save(commit=False)
                reiv_atualizada.responsavel_admin = request.user

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


# ==============================================================================
# 6. PERFIL E SEGURANÇA DO SERVIDOR AUTENTICADO
# ==============================================================================


@servidor_required
def servidor_visualizar_meu_perfil(request):
    perfil = _obter_perfil_servidor(request)
    if not perfil:
        messages.error(request, "Acesso negado. Apenas servidores podem acessar esta página.")
        return redirect("login")

    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Você não possui vínculo com nenhuma instituição ativa.")
        return redirect("login")

    total_itens_registrados = Item.objects.filter(
        instituicao=instituicao,
        usuario_registro=perfil,
    ).count()

    total_reivindicacoes_atendidas = Reivindicacao.objects.filter(
        instituicao=instituicao,
        responsavel_admin=perfil,
    ).count()

    context = {
        "instituicao": instituicao,
        "perfil": perfil,
        "usuario": request.user,
        "total_itens_registrados": total_itens_registrados,
        "total_reivindicacoes_atendidas": total_reivindicacoes_atendidas,
    }
    return render(request, "serv/meu_perfil.html", context)


@servidor_required
def servidor_editar_meu_perfil(request):
    perfil = _obter_perfil_servidor(request)
    if not perfil:
        messages.error(request, "Acesso negado. Apenas servidores podem acessar esta página.")
        return redirect("servidor_painel")

    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Nenhuma instituição ativa associada à sua sessão.")
        return redirect("servidor_painel")

    if request.method == "POST":
        user_form = ServidorEditarUserForm(
            request.POST,
            request.FILES,
            instance=perfil,
            instituicao=instituicao,
        )

        if user_form.is_valid():
            with transaction.atomic():
                perfil_salvo = user_form.save()

            request.session["primeiro_nome"] = perfil_salvo.primeiro_nome
            request.session["foto_url"] = perfil_salvo.foto.url if perfil_salvo.foto else None

            messages.success(request, "Seus dados de perfil foram atualizados com sucesso.")
            return redirect("servidor_visualizar_meu_perfil")

        messages.error(request, "Corrija os erros destacados no formulário antes de salvar.")
    else:
        user_form = ServidorEditarUserForm(instance=perfil, instituicao=instituicao)

    context = {
        "perfil": perfil,
        "instituicao": instituicao,
        "user_form": user_form,
    }
    return render(request, "serv/editar_meu_perfil.html", context)


@servidor_required
def servidor_alterar_senha(request):
    perfil = _obter_perfil_servidor(request)
    if not perfil:
        messages.error(request, "Acesso negado. Apenas servidores podem acessar esta página.")
        return redirect("servidor_painel")

    if request.method == "POST":
        form = ServidorAlterarSenhaForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Sua senha foi alterada com sucesso.")
            return redirect("servidor_visualizar_meu_perfil")

        messages.error(request, "Não foi possível alterar a senha. Verifique os erros abaixo.")
    else:
        form = ServidorAlterarSenhaForm(user=request.user)

    context = {
        "perfil": perfil,
        "form": form,
    }
    return render(request, "serv/alterar_senha.html", context)