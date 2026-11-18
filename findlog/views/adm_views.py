from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render

from ..decorators import superuser_required
from ..forms.categoria import CategoriaForm
from ..forms.instituicao import InstituicaoForm, InstituicaoUpdateForm
from ..forms.item import ItemUpdateForm
from ..forms.perfil import (
    AutoCadastroServidorForm,
    AutoCadastroUsuarioForm,
    EditarMeuPerfilForm,
    NovoUsuarioForm,
    TrocarMinhaSenhaForm,
)
from ..forms.reivindicacao import ReivindicacaoUpdateForm
from ..forms.sala import SalaForm
from ..models import Categoria, Contato, Instituicao, Item, Perfil, Reivindicacao, Sala
from ..utils import (
    _obter_instituicao_por_token,
    apenas_digitos,
    exibir_erros_formulario,
    gerar_slug_unico,
    higienizar_dados_post,
    paginar_queryset,
    verificar_acesso_admin,
)


# ==============================================================================
# DASHBOARD
# ==============================================================================


@superuser_required
def dashboard_adm(request):
    context = {
        "total_instituicoes": Instituicao.objects.count(),
        "total_categorias": Categoria.objects.count(),
        "total_usuarios": Perfil.objects.count(),
        "total_salas": Sala.objects.count(),
        "total_itens": Item.objects.count(),
        "total_contatos": Contato.objects.count(),
    }
    return render(request, "adm/dashboard.html", context)


# ==============================================================================
# INSTITUIÇÕES
# ==============================================================================


@superuser_required
def nova_instituicao(request):
    if request.method == "POST":
        dados_post = higienizar_dados_post(request.POST, campos=("cnpj", "telefone"))
        form = InstituicaoForm(dados_post)

        if form.is_valid():
            instituicao = form.save(commit=False)
            instituicao.ativo = True
            instituicao.save()
            messages.success(request, f"Instituição '{instituicao.nome}' cadastrada com sucesso!")
            return redirect("lista_instituicoes")

        messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = InstituicaoForm()

    return render(request, "adm/nova_instituicao.html", {"form": form})


@superuser_required
def lista_instituicoes(request):
    termo_busca = request.GET.get("q", "").strip()
    instituicoes_query = Instituicao.objects.all().order_by("-data_criacao")

    if termo_busca:
        digitos_busca = apenas_digitos(termo_busca)
        filtro = Q(nome__icontains=termo_busca) | Q(endereco__icontains=termo_busca)
        if digitos_busca:
            filtro |= Q(cnpj__icontains=digitos_busca)
        instituicoes_query = instituicoes_query.filter(filtro)

    instituicoes_paginadas = paginar_queryset(request, instituicoes_query, por_pagina=10)

    context = {
        "instituicoes": instituicoes_paginadas,
        "q": termo_busca,
        "page": instituicoes_paginadas.number,
        "total_pages": instituicoes_paginadas.paginator.num_pages,
    }
    return render(request, "adm/instituicoes.html", context)


@superuser_required
def detalhes_instituicao(request, cnpj):
    instituicao = get_object_or_404(Instituicao, pk=cnpj)
    return render(request, "adm/detalhes_instituicao.html", {"instituicao": instituicao})


@superuser_required
def editar_instituicao(request, cnpj):
    instituicao = get_object_or_404(Instituicao, pk=cnpj)

    if request.method == "POST":
        form = InstituicaoUpdateForm(request.POST, instance=instituicao)
        if form.is_valid():
            form.save()
            messages.success(request, f"Instituição '{instituicao.nome}' atualizada com sucesso!")
            return redirect("lista_instituicoes")

        exibir_erros_formulario(request, form)
    else:
        form = InstituicaoUpdateForm(instance=instituicao)

    return render(
        request, "adm/editar_instituicao.html", {"form": form, "instituicao": instituicao}
    )


@superuser_required
def excluir_instituicao(request, cnpj):
    instituicao = get_object_or_404(Instituicao, pk=cnpj)
    nome = instituicao.nome
    instituicao.delete()
    messages.success(request, f"A instituição '{nome}' foi excluída com sucesso.")
    return redirect("lista_instituicoes")


# ==============================================================================
# CATEGORIAS
# ==============================================================================


@superuser_required
def lista_categorias(request):
    termo_busca = request.GET.get("q", "").strip()
    categorias_query = Categoria.objects.all().order_by("nome")

    if termo_busca:
        categorias_query = categorias_query.filter(
            Q(nome__icontains=termo_busca)
            | Q(codigo__iexact=termo_busca)
            | Q(descricao__icontains=termo_busca)
        )

    context = {
        "categorias": paginar_queryset(request, categorias_query, por_pagina=10),
        "q": termo_busca,
    }
    return render(request, "adm/categorias.html", context)


@superuser_required
def nova_categoria(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f"Categoria '{categoria.nome}' cadastrada com sucesso!")
            return redirect("lista_categorias")

        exibir_erros_formulario(request, form)
    else:
        form = CategoriaForm()

    return render(request, "adm/nova_categoria.html", {"form": form})


@superuser_required
def atualizar_categoria(request, codigo):
    categoria = get_object_or_404(Categoria, pk=codigo)

    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.ativa = request.POST.get("ativo") == "1"
            cat.slug = gerar_slug_unico(Categoria, cat, campo_origem="nome", campo_slug="slug")
            cat.save()

            messages.success(request, f"Categoria '{cat.nome}' atualizada com sucesso!")
            return redirect("lista_categorias")

        exibir_erros_formulario(request, form)
    else:
        form = CategoriaForm(instance=categoria)

    return render(request, "adm/editar_categoria.html", {"form": form, "categoria": categoria})


@superuser_required
def excluir_categoria(request, codigo):
    categoria = get_object_or_404(Categoria, pk=codigo)
    nome = categoria.nome

    try:
        categoria.delete()
        messages.success(request, f"A categoria '{nome}' foi excluída com sucesso.")
    except ProtectedError:
        messages.error(
            request,
            f"Não é possível excluir a categoria '{nome}', pois existem itens vinculados a ela. "
            "Realoque ou remova os itens antes de tentar novamente, ou desative a categoria.",
        )

    return redirect("lista_categorias")


@superuser_required
def view_categoria(request, codigo):
    categoria = get_object_or_404(Categoria, pk=codigo)
    return render(request, "adm/detalhes_categoria.html", {"categoria": categoria})


# ==============================================================================
# CONTATOS
# ==============================================================================


@superuser_required
def lista_contatos(request):
    termo_busca = request.GET.get("q", "").strip()
    contatos_query = Contato.objects.all().order_by("-data")

    if termo_busca:
        contatos_query = contatos_query.filter(
            Q(nome__icontains=termo_busca)
            | Q(email__icontains=termo_busca)
            | Q(assunto__icontains=termo_busca)
            | Q(mensagem__icontains=termo_busca)
        )

    context = {
        "contatos": paginar_queryset(request, contatos_query, por_pagina=10),
        "q": termo_busca,
    }
    return render(request, "adm/contatos.html", context)


@superuser_required
def view_contato(request, uuid):
    contato = get_object_or_404(Contato, uuid=uuid)
    return render(request, "adm/detalhes_contato.html", {"contato": contato})


@superuser_required
def apagar_contato(request, uuid):
    contato = get_object_or_404(Contato, uuid=uuid)
    nome = contato.nome or "Contato anônimo"
    contato.delete()
    messages.success(request, f"Mensagem de '{nome}' excluída com sucesso.")
    return redirect("lista_contatos")


# ==============================================================================
# USUÁRIOS (ADMINISTRAÇÃO)
# ==============================================================================


@superuser_required
def novo_usuario(request):
    bloqueio = verificar_acesso_admin(
        request, mensagem="Acesso não autorizado para cadastrar novos usuários."
    )
    if bloqueio:
        return bloqueio

    if request.method == "POST":
        dados_post = higienizar_dados_post(request.POST, campos=("cpf", "telefone"))
        form = NovoUsuarioForm(dados_post, request.FILES)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request, f"Usuário '{usuario.nome or usuario.email}' cadastrado com sucesso!"
            )
            return redirect("lista_usuarios")

        messages.error(
            request, "Não foi possível cadastrar o usuário. Corrija os erros apontados."
        )
    else:
        form = NovoUsuarioForm()

    context = {
        "form": form,
        "instituicoes": Instituicao.objects.filter(ativo=True).order_by("nome"),
        "salas": Sala.objects.filter(ativa=True),
        "tipos_usuario": Perfil.TipoUsuario.choices,
    }
    return render(request, "adm/novo_usuario.html", context)


@superuser_required
def lista_usuarios(request):
    bloqueio = verificar_acesso_admin(request, mensagem="Acesso restrito a administradores.")
    if bloqueio:
        return bloqueio

    termo_busca = request.GET.get("q", "").strip()
    usuarios_query = Perfil.objects.all().order_by("-date_joined")

    if termo_busca:
        digitos_cpf = apenas_digitos(termo_busca)
        filtro = (
            Q(nome__icontains=termo_busca)
            | Q(email__icontains=termo_busca)
            | Q(username__icontains=termo_busca)
        )
        if digitos_cpf:
            filtro |= Q(cpf__icontains=digitos_cpf)
        usuarios_query = usuarios_query.filter(filtro)

    context = {
        "usuarios": paginar_queryset(request, usuarios_query, por_pagina=10),
        "q": termo_busca,
    }
    return render(request, "adm/usuarios.html", context)


@superuser_required
def alternar_status_usuario(request, pk):
    bloqueio = verificar_acesso_admin(request)
    if bloqueio:
        return bloqueio

    usuario = get_object_or_404(Perfil, pk=pk)
    if usuario == request.user:
        messages.warning(request, "Você não pode desativar seu próprio usuário logado.")
        return redirect("lista_usuarios")

    novo_status = not usuario.ativo
    usuario.ativo = novo_status
    usuario.is_active = novo_status
    usuario.save(update_fields=["ativo", "is_active"])

    status_str = "ativado" if novo_status else "desativado"
    messages.success(
        request, f"O usuário '{usuario.nome or usuario.email}' foi {status_str} com sucesso."
    )
    return redirect("lista_usuarios")


@superuser_required
def ativar_usuario(request, pk):
    bloqueio = verificar_acesso_admin(request)
    if bloqueio:
        return bloqueio

    usuario = get_object_or_404(Perfil, pk=pk)
    usuario.ativo = True
    usuario.is_active = True
    usuario.save(update_fields=["ativo", "is_active"])
    messages.success(request, f"Usuário '{usuario.nome or usuario.email}' ativado com sucesso.")
    return redirect("lista_usuarios")


@superuser_required
def desativar_usuario(request, pk):
    bloqueio = verificar_acesso_admin(request)
    if bloqueio:
        return bloqueio

    usuario = get_object_or_404(Perfil, pk=pk)
    if usuario == request.user:
        messages.warning(request, "Você não pode desativar a sua própria conta.")
        return redirect("lista_usuarios")

    usuario.ativo = False
    usuario.is_active = False
    usuario.save(update_fields=["ativo", "is_active"])
    messages.warning(request, f"Usuário '{usuario.nome or usuario.email}' desativado.")
    return redirect("lista_usuarios")


@superuser_required
def excluir_usuario(request, pk):
    bloqueio = verificar_acesso_admin(request)
    if bloqueio:
        return bloqueio

    usuario = get_object_or_404(Perfil, pk=pk)
    if usuario == request.user:
        messages.error(request, "Não é permitido excluir o usuário atualmente autenticado.")
        return redirect("lista_usuarios")

    nome = usuario.nome or usuario.email
    usuario.delete()
    messages.success(request, f"Conta de '{nome}' excluída definitivamente.")
    return redirect("lista_usuarios")


@superuser_required
def visualizar_usuario(request, pk):
    usuario = get_object_or_404(Perfil, pk=pk)
    return render(request, "adm/detalhe_usuario.html", {"usuario": usuario})


# ==============================================================================
# SALAS E AMBIENTES
# ==============================================================================


@superuser_required
def lista_salas(request):
    bloqueio = verificar_acesso_admin(request, mensagem="Acesso restrito a administradores.")
    if bloqueio:
        return bloqueio

    termo_busca = request.GET.get("q", "").strip()
    salas_query = Sala.objects.all()

    if termo_busca:
        filtro = (
            Q(nome__icontains=termo_busca)
            | Q(predio__icontains=termo_busca)
            | Q(andar__icontains=termo_busca)
        )
        if hasattr(Sala, "codigo"):
            filtro |= Q(codigo__icontains=termo_busca)
        salas_query = salas_query.filter(filtro)

    context = {
        "salas": paginar_queryset(request, salas_query, por_pagina=10),
        "q": termo_busca,
    }
    return render(request, "adm/salas.html", context)


@superuser_required
def nova_sala(request):
    bloqueio = verificar_acesso_admin(request)
    if bloqueio:
        return bloqueio

    if request.method == "POST":
        form = SalaForm(request.POST)
        if form.is_valid():
            sala = form.save()
            messages.success(request, f"Sala {sala.nome} ({sala.predio}) cadastrada com sucesso!")
            return redirect("lista_salas")
        messages.error(request, "Erro ao cadastrar sala. Verifique os dados informados.")
    else:
        form = SalaForm(initial={"ativa": True})

    return render(request, "adm/nova_sala.html", {"form": form, "acao": "Nova Sala"})


@superuser_required
def detalhes_sala(request, codigo):
    sala = get_object_or_404(Sala, pk=codigo)
    servidores = Perfil.objects.filter(sala=sala, tipo=Perfil.TipoUsuario.SERVIDOR)
    return render(
        request,
        "adm/detalhes_sala.html",
        {"sala": sala, "servidores": servidores},
    )


@superuser_required
def editar_sala(request, codigo):
    bloqueio = verificar_acesso_admin(request)
    if bloqueio:
        return bloqueio

    sala = get_object_or_404(Sala, pk=codigo)

    if request.method == "POST":
        form = SalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            messages.success(request, f"Sala {sala.nome} atualizada com sucesso!")
            return redirect("lista_salas")
        messages.error(request, "Não foi possível atualizar a sala. Verifique os campos.")
    else:
        form = SalaForm(instance=sala)

    return render(
        request,
        "adm/editar_sala.html",
        {"form": form, "sala": sala, "acao": "Editar Sala"},
    )


@superuser_required
def alternar_status_sala(request, codigo):
    bloqueio = verificar_acesso_admin(request)
    if bloqueio:
        return bloqueio

    sala = get_object_or_404(Sala, pk=codigo)
    campo_status = "ativa" if hasattr(sala, "ativa") else "ativo"
    status_atual = getattr(sala, campo_status, True)
    setattr(sala, campo_status, not status_atual)
    sala.save(update_fields=[campo_status])

    novo_status_str = "ativada" if getattr(sala, campo_status) else "desativada"
    messages.success(request, f"A Sala {sala.nome} foi {novo_status_str} com sucesso.")
    return redirect("lista_salas")


@superuser_required
def excluir_sala(request, codigo):
    bloqueio = verificar_acesso_admin(request)
    if bloqueio:
        return bloqueio

    sala = get_object_or_404(Sala, pk=codigo)
    nome_sala = f"Sala {sala.nome} ({sala.predio})"

    try:
        sala.delete()
        messages.success(request, f"{nome_sala} excluída definitivamente.")
    except ProtectedError:
        messages.error(
            request,
            f"Não é possível excluir a {nome_sala}, pois existem itens ou servidores vinculados a ela. "
            "Remova ou transfira os vínculos antes de excluir, ou apenas desative a sala.",
        )

    return redirect("lista_salas")


# ==============================================================================
# ITENS
# ==============================================================================


@superuser_required
def lista_itens(request):
    termo_busca = request.GET.get("q", "").strip()
    status_filtro = request.GET.get("status", "").strip()

    itens_query = Item.objects.select_related("categoria", "instituicao", "local").order_by(
        "-data_registro"
    )

    if termo_busca:
        itens_query = itens_query.filter(
            Q(nome__icontains=termo_busca)
            | Q(codigo__iexact=termo_busca)
            | Q(marca_ou_modelo__icontains=termo_busca)
            | Q(descricao__icontains=termo_busca)
            | Q(cor__icontains=termo_busca)
        )

    if status_filtro.isdigit():
        itens_query = itens_query.filter(status=int(status_filtro))

    context = {
        "itens": paginar_queryset(request, itens_query, por_pagina=10),
        "q": termo_busca,
        "status_filtro": status_filtro,
        "status_choices": Item.StatusItem.choices,
    }
    return render(request, "adm/itens.html", context)


@superuser_required
def detalhes_item(request, uuid):
    item = get_object_or_404(
        Item.objects.select_related(
            "categoria", "instituicao", "local", "local_guardado", "usuario_registro", "dono"
        ),
        uuid=uuid,
    )
    reivindicacoes = item.reivindicacoes.select_related("autor").order_by("-data")
    return render(
        request, "adm/detalhes_item.html", {"item": item, "reivindicacoes": reivindicacoes}
    )


@superuser_required
def atualizar_item(request, uuid):
    item = get_object_or_404(Item, uuid=uuid)

    if request.method == "POST":
        form = ItemUpdateForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item_salvo = form.save()
            messages.success(request, f"Item '{item_salvo}' atualizado com sucesso!")
            return redirect("detalhes_item", uuid=item.uuid)
        messages.error(request, "Não foi possível salvar as alterações. Verifique os campos.")
    else:
        form = ItemUpdateForm(instance=item)

    return render(request, "adm/editar_item.html", {"form": form, "item": item})


@superuser_required
def apagar_item(request, uuid):
    item = get_object_or_404(Item, uuid=uuid)
    identificador = str(item)

    try:
        item.delete()
        messages.success(request, f"{identificador} excluído com sucesso.")
    except ProtectedError:
        messages.error(
            request,
            f"Não é possível excluir o {identificador}, pois há vínculos protegidos associados a ele.",
        )

    return redirect("lista_itens")


# ==============================================================================
# REIVINDICAÇÕES
# ==============================================================================


@superuser_required
def lista_reivindicacoes(request):
    termo_busca = request.GET.get("q", "").strip()
    status_filtro = request.GET.get("status", "").strip()

    reivindicacoes_query = Reivindicacao.objects.select_related(
        "autor", "item", "instituicao"
    ).order_by("-data")

    if termo_busca:
        protocolo_limpo = termo_busca.lstrip("#")
        filtro_busca = (
            Q(autor__nome__icontains=termo_busca)
            | Q(autor__email__icontains=termo_busca)
            | Q(item__nome__icontains=termo_busca)
            | Q(item__codigo__iexact=termo_busca)
            | Q(pedido__icontains=termo_busca)
        )
        if protocolo_limpo.isdigit():
            filtro_busca |= Q(protocolo=int(protocolo_limpo))
        reivindicacoes_query = reivindicacoes_query.filter(filtro_busca)

    if status_filtro.isdigit() and int(status_filtro) in Reivindicacao.StatusReivindicacao.values:
        reivindicacoes_query = reivindicacoes_query.filter(status=int(status_filtro))

    context = {
        "reivindicacoes": paginar_queryset(request, reivindicacoes_query, por_pagina=10),
        "q": termo_busca,
        "status_filtro": status_filtro,
        "status_choices": Reivindicacao.StatusReivindicacao.choices,
    }
    return render(request, "adm/reivindicacoes.html", context)


@superuser_required
def detalhes_reivindicacao(request, protocolo):
    reivindicacao = get_object_or_404(
        Reivindicacao.objects.select_related(
            "autor", "item", "instituicao", "responsavel_admin", "local_devolucao"
        ),
        protocolo=protocolo,
    )
    return render(request, "adm/detalhes_reivindicacao.html", {"reivindicacao": reivindicacao})


@superuser_required
def atualizar_reivindicacao(request, protocolo):
    reivindicacao = get_object_or_404(Reivindicacao, protocolo=protocolo)

    if request.method == "POST":
        form = ReivindicacaoUpdateForm(request.POST, instance=reivindicacao)
        if form.is_valid():
            reiv = form.save(commit=False)

            if not reiv.responsavel_admin and request.user.tipo == Perfil.TipoUsuario.ADMINISTRADOR:
                reiv.responsavel_admin = request.user

            if reiv.status == Reivindicacao.StatusReivindicacao.CONCLUIDA:
                reiv.item.status = Item.StatusItem.DEVOLVIDO
                reiv.item.dono = reiv.autor
                if reiv.data_devolucao:
                    reiv.item.data_devolucao = reiv.data_devolucao
                reiv.item.save(update_fields=["status", "dono", "data_devolucao"])

            reiv.save()
            messages.success(request, f"Reivindicação #{reiv.protocolo} atualizada com sucesso!")
            return redirect("detalhes_reivindicacao", protocolo=reiv.protocolo)

        messages.error(request, "Erro ao atualizar a reivindicação. Verifique os campos.")
    else:
        form = ReivindicacaoUpdateForm(instance=reivindicacao)

    return render(
        request, "adm/editar_reivindicacao.html", {"form": form, "reivindicacao": reivindicacao}
    )


@superuser_required
def apagar_reivindicacao(request, protocolo):
    reivindicacao = get_object_or_404(Reivindicacao, protocolo=protocolo)
    num_protocolo = reivindicacao.protocolo
    reivindicacao.delete()
    messages.success(request, f"Reivindicação #{num_protocolo} removida com sucesso.")
    return redirect("lista_reivindicacoes")


# ==============================================================================
# PERFIL DO ADMINISTRADOR
# ==============================================================================


@superuser_required
def meu_perfil(request):
    return render(request, "adm/meu_perfil.html", {"usuario": request.user})


@superuser_required
def editar_meu_perfil(request):
    usuario = request.user
    if request.method == "POST":
        form = EditarMeuPerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            usuario_salvo = form.save()

            request.session["username"] = usuario_salvo.username
            request.session["primeiro_nome"] = usuario_salvo.primeiro_nome
            request.session["foto_url"] = usuario_salvo.foto.url if usuario_salvo.foto else None

            messages.success(request, "Seus dados foram atualizados com sucesso!")
            return redirect("meu_perfil")
        messages.error(request, "Erro ao atualizar seus dados. Verifique os campos.")
    else:
        form = EditarMeuPerfilForm(instance=usuario)

    return render(request, "adm/editar_perfil.html", {"form": form, "usuario": usuario})


@superuser_required
def trocar_minha_senha(request):
    if request.method == "POST":
        form = TrocarMinhaSenhaForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Sua senha foi alterada com sucesso!")
            return redirect("meu_perfil")
        messages.error(request, "Não foi possível alterar sua senha. Confira os requisitos abaixo.")
    else:
        form = TrocarMinhaSenhaForm(user=request.user)

    return render(request, "adm/trocar_senha.html", {"form": form})


# ==============================================================================
# AUTOCADASTRO PÚBLICO POR CONVITE ASSINADO
# ==============================================================================


def novo_usuario_instituicao(request, token):
    """Link público com token assinado para autocadastro de Usuários Comuns."""
    if request.user.is_authenticated:
        messages.info(request, "Você já está autenticado no sistema.")
        return redirect("login")

    instituicao = _obter_instituicao_por_token(token)

    if request.method == "POST":
        dados_post = higienizar_dados_post(request.POST, campos=("cpf", "telefone"))
        form = AutoCadastroUsuarioForm(dados_post, instituicao=instituicao)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Cadastro realizado com sucesso na unidade {instituicao.nome}! "
                "Faça login abaixo utilizando o e-mail e a senha cadastrados.",
            )
            return redirect("login")

        messages.error(
            request, "Não foi possível concluir seu cadastro. Verifique os campos destacados."
        )
    else:
        form = AutoCadastroUsuarioForm(instituicao=instituicao)

    context = {
        "form": form,
        "instituicao": instituicao,
        "token": token,
        "tipo_cadastro": "Usuário",
    }
    return render(request, "public/autocadastro_usuario.html", context)


def novo_servidor_instituicao(request, token):
    """Link público com token assinado para autocadastro de Servidores (aguarda aprovação)."""
    if request.user.is_authenticated:
        messages.info(request, "Você já está autenticado no sistema.")
        return redirect("login")

    instituicao = _obter_instituicao_por_token(token)

    if request.method == "POST":
        dados_post = higienizar_dados_post(request.POST, campos=("cpf", "telefone"))
        form = AutoCadastroServidorForm(dados_post, instituicao=instituicao)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Solicitação de cadastro enviada com sucesso para {instituicao.nome}! "
                "Por segurança, seu acesso passará por aprovação da administração da unidade antes do primeiro login.",
            )
            return redirect("login")

        messages.error(
            request, "Não foi possível concluir o cadastro. Verifique os campos destacados."
        )
    else:
        form = AutoCadastroServidorForm(instituicao=instituicao)

    context = {
        "form": form,
        "instituicao": instituicao,
        "token": token,
        "tipo_cadastro": "Servidor",
    }
    return render(request, "public/autocadastro_servidor.html", context)