from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.urls import reverse

from ..utils import (
    gerar_qrcode_base64,
    apenas_digitos,
    _obter_perfil_servidor,
    _obter_instituicao_servidor,
    redirecionar_origem,
)
from ..forms.reivindicacao import ServidorAnaliseReivindicacaoForm
from ..forms.sala import ServidorSalaForm, ServidorUpdateSalaForm
from ..forms.perfil import (
    ServidorCadastroColegaForm,
    ServidorAlterarSenhaForm,
    ServidorEditarUserForm,
)
from ..forms.item import ServidorItemForm, ServidorAtualizarItemForm


from ..models import Perfil, Sala, Categoria, Item, Reivindicacao
from ..decorators import servidor_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.db.models import Q
import re


def _obter_instituicao_ativa(request):
    """Retorna a instituição ativa da sessão ou o primeiro vínculo ativo do usuário."""
    cnpj_sessao = request.session.get("instituicao_cnpj")
    usuario = request.user

    instituicao = None
    if cnpj_sessao:
        instituicao = usuario.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = usuario.instituicao.filter(ativo=True).first()

    return instituicao


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


@servidor_required
def servidor_painel(request):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = None

    if cnpj_sessao:
        instituicao = request.user.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()

    if not instituicao:
        instituicao = request.user.instituicao.filter(ativo=True).first()

    if not instituicao:
        messages.error(request, "Você não possui vínculo com nenhuma instituição ativa.")
        return redirect("login")

    # Contagens métricas para os cards do dashboard
    qtde_reivindicacoes = Reivindicacao.objects.filter(instituicao=instituicao).count()
    qtde_itens = Item.objects.filter(instituicao=instituicao).count()
    qtde_usuarios = Perfil.objects.filter(
        instituicao=instituicao, tipo=Perfil.TipoUsuario.USUARIO
    ).count()
    qtde_servidores = Perfil.objects.filter(
        instituicao=instituicao, tipo=Perfil.TipoUsuario.SERVIDOR
    ).count()
    qtde_salas = Sala.objects.filter(instituicao=instituicao).count()

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

    qrcode_usuario = gerar_qrcode_base64(link_convite_usuario)
    qrcode_servidor = gerar_qrcode_base64(link_convite_servidor)

    context = {
        "instituicao": instituicao,
        "qtde_reivindicacoes": qtde_reivindicacoes,
        "qtde_itens": qtde_itens,
        "qtde_usuarios": qtde_usuarios,
        "qtde_servidores": qtde_servidores,
        "qtde_salas": qtde_salas,
        "ultimos_itens": ultimos_itens,
        "link_convite_usuario": link_convite_usuario,
        "link_convite_servidor": link_convite_servidor,
        "qrcode_usuario": qrcode_usuario,
        "qrcode_servidor": qrcode_servidor,
    }

    return render(request, "serv/index.html", context)


@servidor_required
def servidor_cadastrar_sala(request):
    usuario = request.user

    # 1. Garante que apenas Servidores (ou Administradores) acessem
    if usuario.tipo != Perfil.TipoUsuario.SERVIDOR and not (
        usuario.tipo == Perfil.TipoUsuario.ADMINISTRADOR or usuario.is_superuser
    ):
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
            sala.ativa = True  # Inicia sempre como ativa
            sala.save()

            messages.success(
                request, f"Sala '{sala.nome}' cadastrada com sucesso na unidade {instituicao.nome}!"
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
            Q(nome__icontains=termo_busca)
            | Q(predio__icontains=termo_busca)
            | Q(codigo__icontains=termo_busca)
            | Q(andar__icontains=termo_busca)
        )

    # Paginação (9 itens por página)
    paginator = Paginator(salas_qs, 9)
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
    instituicao = _obter_instituicao_ativa(request)

    if not instituicao:
        messages.error(request, "Vínculo institucional não encontrado para este usuário.")
        return redirect("servidor_painel")

    # Garante que a sala pertence obrigatoriamente à instituição do servidor
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
    """
    Alterna o status da sala (ativa/inativa) de forma atômica via requisição POST
    e retorna para a página de origem.
    """
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


@servidor_required
def servidor_detalhar_sala(request, codigo):
    instituicao = _obter_instituicao_ativa(request)

    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)

    context = {"sala": sala}

    return render(request, "serv/detalhar_sala.html", context)


@servidor_required
def servidor_listar_itens(request):
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = (
        request.user.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()
        if cnpj_sessao
        else request.user.instituicao.filter(ativo=True).first()
    )
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    itens_qs = (
        Item.objects.filter(instituicao=instituicao)
        .select_related("categoria", "local", "local_guardado", "usuario_registro")
        .order_by("-data_registro")
    )

    # Filtro de busca textual
    q = request.GET.get("q", "").strip()
    if q:
        itens_qs = itens_qs.filter(
            Q(nome__icontains=q)
            | Q(codigo__icontains=q)
            | Q(descricao__icontains=q)
            | Q(marca_ou_modelo__icontains=q)
            | Q(cor__icontains=q)
        )

    # Filtro opcional por Categoria
    categoria_filtro = request.GET.get("categoria", "").strip()
    if categoria_filtro:
        itens_qs = itens_qs.filter(categoria_id=categoria_filtro)

    # Filtro opcional por Status
    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit():
        itens_qs = itens_qs.filter(status=int(status_filtro))

    # Filtro opcional: Apenas itens cadastrados pelo servidor autenticado
    apenas_meus_itens = request.GET.get("meus_itens", "").strip() == "1"
    if apenas_meus_itens:
        itens_qs = itens_qs.filter(usuario_registro=request.user)

    paginator = Paginator(itens_qs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

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
        "total_itens": paginator.count,
    }
    return render(request, "serv/listar_itens.html", context)


# ----------------------------------------------------------------------
# 2. LISTAR ITENS POR SALA (Onde foi encontrado ou guardado)
# ----------------------------------------------------------------------
@servidor_required
def servidor_itens_por_sala(request, sala_codigo):
    instituicao = _obter_instituicao_ativa(request)

    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    sala = get_object_or_404(Sala, codigo=sala_codigo, instituicao=instituicao)

    # Considera o item associado à sala onde foi achado OU onde está guardado
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
    """
    Lista paginada de todos os usuários e servidores vinculados
    à instituição ativa na sessão do servidor autenticado.
    """
    cnpj_sessao = request.session.get("instituicao_cnpj")
    instituicao = (
        request.user.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()
        if cnpj_sessao
        else request.user.instituicao.filter(ativo=True).first()
    )

    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    # Tipos permitidos na visualização institucional (exclui Administradores globais)
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
        .order_by(
            "ativo", "-criado_em"
        )  # Pendentes (ativo=False) aparecem no topo para fácil aprovação
    )

    # 1. Busca textual (nome, e-mail, username, código/matrícula, CPF e telefone)
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

    # 2. Filtro por Tipo de Perfil (Usuário ou Servidor)
    tipo_filtro = request.GET.get("tipo", "").strip()
    if tipo_filtro.isdigit() and int(tipo_filtro) in [
        Perfil.TipoUsuario.USUARIO,
        Perfil.TipoUsuario.SERVIDOR,
    ]:
        perfis_qs = perfis_qs.filter(tipo=int(tipo_filtro))

    # 3. Filtro opcional por Status (Ativo / Pendente-Inativo)
    status_filtro = request.GET.get("status", "").strip()
    if status_filtro == "ativo":
        perfis_qs = perfis_qs.filter(ativo=True)
    elif status_filtro == "inativo":
        perfis_qs = perfis_qs.filter(ativo=False)

    # Paginação
    paginator = Paginator(perfis_qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "titulo": "Usuários & Equipe da Unidade",
        "subtitulo": f"Perfis vinculados à instituição: {instituicao.nome}",
        "instituicao": instituicao,
        "page_obj": page_obj,
        "termo_busca": q,
        "tipo_filtro": tipo_filtro,
        "status_filtro": status_filtro,
        "tipos_choices": tipos_permitidos,
        "total_perfis": paginator.count,
    }
    return render(request, "serv/usuarios_instituicao.html", context)


@servidor_required
def servidor_visualizar_usuario(request, username):
    """
    Exibe os detalhes cadastrais, histórico de reivindicações (se usuário)
    ou itens registrados (se servidor) dentro da instituição ativa.
    """
    instituicao = _obter_instituicao_servidor(request)
    if not instituicao:
        messages.error(request, "Nenhuma instituição associada ao seu perfil.")
        return redirect("login")

    perfil = _obter_perfil_da_instituicao(instituicao, username)

    # Histórico contextualizado na unidade atual
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
    """
    Ativa o acesso de um usuário ou aprova o cadastro pendente de um servidor
    vinculado à instituição ativa.
    """
    instituicao = _obter_instituicao_servidor(request)
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

    proxima_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if proxima_url:
        return redirect(proxima_url)
    return redirect("servidor_usuarios_instituicao")


@servidor_required
@require_POST
def servidor_desativar_usuario(request, username):
    """
    Bloqueia temporariamente o acesso de um usuário ou servidor vinculado
    à instituição ativa.
    """
    instituicao = _obter_instituicao_servidor(request)
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
        perfil.save(update_fields=["ativo"])
        papel = "Servidor" if perfil.tipo == Perfil.TipoUsuario.SERVIDOR else "Usuário"
        messages.warning(
            request,
            f"O acesso de {papel.lower()} {perfil.nome or perfil.username} foi desativado.",
        )

    proxima_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if proxima_url:
        return redirect(proxima_url)
    return redirect("servidor_usuarios_instituicao")


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
            item.instituicao = instituicao  # Garante o vínculo com a instituição ativa
            item.usuario_registro = usuario  # Servidor responsável pelo cadastro
            item.save()

            messages.success(
                request,
                f"Item '{item.nome or item.codigo}' cadastrado com sucesso! Código gerado: {item.codigo}",
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
def servidor_detalhes_item(request, uuid):
    """
    Exibe os detalhes completos de um item da instituição ativa do servidor
    (localizado pelo UUID) e lista todas as reivindicações registradas para
    este objeto, com filtro por status e paginação.
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

    # Busca o item pelo UUID garantindo que pertence à instituição do servidor
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

    # Lista todas as reivindicações vinculadas a este item
    reivindicacoes_qs = (
        Reivindicacao.objects.filter(item=item, instituicao=instituicao)
        .select_related("autor", "responsavel_admin", "local_devolucao")
        .order_by("-data")
    )

    # Filtro opcional por status da reivindicação
    status_filtro = request.GET.get("status", "").strip()
    if status_filtro.isdigit() and int(status_filtro) in Reivindicacao.StatusReivindicacao.values:
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
@require_POST
def servidor_apagar_item(request, uuid):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    # Busca o item pelo UUID e restringe à instituição do servidor logado
    item = get_object_or_404(Item, uuid=uuid, instituicao=instituicao)

    # Trava de segurança: impede apagar itens já devolvidos para não perder histórico
    if item.status == Item.StatusItem.DEVOLVIDO:
        messages.warning(request, "Não é possível apagar um item que já foi devolvido.")
        return redirect("servidor_detalhes_item", uuid=item.uuid)

    nome_item = item.nome or item.codigo
    item.delete()

    messages.success(request, f'O item "{nome_item}" foi removido com sucesso.')
    return redirect("servidor_listar_itens")


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


@servidor_required
def servidor_atualizar_item(request, uuid):
    instituicao = _obter_instituicao_ativa(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect("servidor_painel")

    # Garante que o item existe e pertence à mesma instituição do servidor
    item = get_object_or_404(Item, uuid=uuid, instituicao=instituicao)

    if request.method == "POST":
        form = ServidorAtualizarItemForm(
            request.POST, request.FILES, instance=item, instituicao=instituicao
        )
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Os dados do item "{item.nome}" foram atualizados com sucesso.'
            )
            return redirect("servidor_detalhes_item", uuid=item.uuid)
        else:
            messages.error(request, "Verifique os erros no formulário antes de salvar.")
    else:
        form = ServidorAtualizarItemForm(instance=item, instituicao=instituicao)

    context = {
        "form": form,
        "item": item,  # Enviado para exibir os campos somente leitura no template
    }
    return render(request, "serv/atualizar_item.html", context)


@servidor_required
def servidor_listar_reivindicacoes(request):
    """
    Inicia exibindo por padrão apenas as reivindicações de itens cadastrados
    pelo servidor autenticado, permitindo alternar para todas as reivindicações
    da unidade através do filtro na interface.
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

    # 3. Filtro: Inicia ativo por padrão (meus_itens=1).
    # Só desativa quando o formulário for submetido com o switch desmarcado (filtrar=1 sem meus_itens=1)
    # ou se ?meus_itens=0 for passado explicitamente na URL.
    meus_itens_param = request.GET.get("meus_itens", "").strip()
    foi_filtrado = request.GET.get("filtrar", "").strip() == "1"

    if meus_itens_param == "0":
        apenas_meus_itens = False
    elif foi_filtrado:
        apenas_meus_itens = meus_itens_param == "1"
    else:
        apenas_meus_itens = True

    if apenas_meus_itens:
        reivindicacoes_qs = reivindicacoes_qs.filter(item__usuario_registro=usuario)

    # 4. Paginação (12 registros por página)
    paginator = Paginator(reivindicacoes_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

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
        "total_reivindicacoes": paginator.count,
    }

    return render(request, "serv/listar_reivindicacoes.html", context)


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

    # Resumo rápido de atividade do servidor para exibir no card do perfil
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

    instituicao = _obter_instituicao_servidor(request)
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

            # Sincroniza os dados atualizados com a sessão (exibidos na topbar/painel)
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
            # Mantém a sessão ativa após a troca de senha
            update_session_auth_hash(request, user)
            messages.success(request, "Sua senha foi alterada com sucesso.")
            return redirect("servidor_visualizar_meu_perfil")
        else:
            messages.error(request, "Não foi possível alterar a senha. Verifique os erros abaixo.")
    else:
        form = ServidorAlterarSenhaForm(user=request.user)

    context = {
        "perfil": perfil,
        "form": form,
    }
    return render(request, "serv/alterar_senha.html", context)
