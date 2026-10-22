from django.shortcuts import render, redirect, get_object_or_404
from .models import Instituicao, Categoria, Perfil, Sala, Item, Contato, Reivindicacao
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, ProtectedError
from .forms import InstituicaoForm, CategoriaForm, NovoUsuarioForm, SalaForm, ItemUpdateForm, ReivindicacaoUpdateForm, EditarMeuPerfilForm, TrocarMinhaSenhaForm
from .utils import apenas_digitos, gerar_slug_unico, redirecionar_por_perfil
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
# Create your views here.


def dashboard_adm(request):
    total_instituicoes = Instituicao.objects.count()
    total_categorias = Categoria.objects.count()
    total_usuarios = Perfil.objects.count()
    total_salas = Sala.objects.count()
    total_itens = Item.objects.count()
    total_contatos = Contato.objects.count()

    context = {
        "total_instituicoes": total_instituicoes,
        "total_categorias": total_categorias,
        "total_usuarios": total_usuarios,
        "total_salas": total_salas,  
        "total_itens": total_itens,
        "total_contatos": total_contatos   
    }

    return render(request, "admin/dashboard.html", context)


def nova_instituicao(request):
    if request.method == "POST":
        # Cria uma cópia mutável do QueryDict
        dados_post = request.POST.copy()

        # Remove caracteres não numéricos
        if 'cnpj' in dados_post:
            dados_post['cnpj'] = apenas_digitos(dados_post['cnpj'])
        if 'telefone' in dados_post:
            dados_post['telefone'] = apenas_digitos(dados_post['telefone'])

        # Instancia o formulário com os dados higienizados
        form = InstituicaoForm(dados_post)

        if form.is_valid():
            instituicao = form.save()
            messages.success(
                request,
                f"Instituição '{instituicao.nome}' cadastrada com sucesso!"
            )
            return redirect("lista_instituicoes")

        messages.error(request, "Por favor, corrija os erros abaixo.")

    else:
        form = InstituicaoForm()

    return render(request, "admin/nova_instituicao.html", {"form": form})


def lista_instituicoes(request):
    termo_busca = request.GET.get("q", "").strip()
    instituicoes_query = Instituicao.objects.all().order_by("-data_criacao")

    if termo_busca:
        digitos_busca = apenas_digitos(termo_busca)
        # Permite busca por texto no nome/endereço ou por dígitos no CNPJ
        filtro = Q(nome__icontains=termo_busca) | Q(endereco__icontains=termo_busca)
        if digitos_busca:
            filtro |= Q(cnpj__icontains=digitos_busca)
        
        instituicoes_query = instituicoes_query.filter(filtro)

    # Paginação: 10 instituições por página
    paginator = Paginator(instituicoes_query, 10)
    pagina = request.GET.get("page", 1)

    try:
        instituicoes_paginadas = paginator.page(pagina)
    except PageNotAnInteger:
        instituicoes_paginadas = paginator.page(1)
    except EmptyPage:
        instituicoes_paginadas = paginator.page(paginator.num_pages)

    context = {
        "instituicoes": instituicoes_paginadas,
        "q": termo_busca,
        "page": instituicoes_paginadas.number,
        "total_pages": paginator.num_pages,
    }
    return render(request, "admin/instituicoes.html", context)

def detalhes_instituicao(request, cnpj):
    instituicao = get_object_or_404(Instituicao, pk=cnpj)
    context = {
        "instituicao": instituicao
    }
    return render(request, "admin/detalhes_instituicao.html",context)


def editar_instituicao(request, cnpj):
    instituicao = get_object_or_404(Instituicao, pk=cnpj)

    if request.method == "POST":
        # Bloqueia alteração manual de CNPJ se for PK
        form = InstituicaoForm(request.POST, instance=instituicao)
        if form.is_valid():
            form.save()
            messages.success(request, f"Instituição '{instituicao.nome}' atualizada com sucesso!")
            return redirect("lista_instituicoes")

        for campo, erros in form.errors.items():
            for erro in erros:
                messages.error(request, f"{campo.capitalize()}: {erro}")
    else:
        form = InstituicaoForm(instance=instituicao)

    return render(
        request,
        "admin/editar_instituicao.html",
        {"form": form, "instituicao": instituicao}
    )

def excluir_instituicao(request, cnpj):
    instituicao = get_object_or_404(Instituicao, pk=cnpj)
    nome = instituicao.nome
    instituicao.delete()
    messages.success(request, f"A instituição '{nome}' foi excluída com sucesso.")
    return redirect("lista_instituicoes")


def lista_categorias(request):
    termo_busca = request.GET.get("q", "").strip()
    categorias_query = Categoria.objects.all().order_by("nome")

    if termo_busca:
        categorias_query = categorias_query.filter(
            Q(nome__icontains=termo_busca) |
            Q(codigo__iexact=termo_busca) |
            Q(descricao__icontains=termo_busca)
        )

    # Paginação: 10 categorias por página
    paginator = Paginator(categorias_query, 10)
    pagina = request.GET.get("page", 1)

    try:
        categorias_paginadas = paginator.page(pagina)
    except PageNotAnInteger:
        categorias_paginadas = paginator.page(1)
    except EmptyPage:
        categorias_paginadas = paginator.page(paginator.num_pages)

    context = {
        "categorias": categorias_paginadas,
        "q": termo_busca,
    }

    return render(request, "admin/categorias.html", context)    


def nova_categoria(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(
                request,
                f"Categoria '{categoria.nome}' cadastrada com sucesso!"
            )
            return redirect("lista_categorias")

        # Repassa os erros de validação via toast / alert messages
        for campo, erros in form.errors.items():
            for erro in erros:
                messages.error(request, f"{campo.capitalize()}: {erro}")
    else:
        form = CategoriaForm()

    return render(request, "admin/nova_categoria.html", {"form": form})


def atualizar_categoria(request, codigo):
    categoria = get_object_or_404(Categoria, pk=codigo)

    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)

        if form.is_valid():
            cat = form.save(commit=False)
            
            # Mapeia o select name="ativo" (valores "1" ou "0") para o campo booleano 'ativa'
            cat.ativa = (request.POST.get("ativo") == "1")

            # Atualiza o slug se o nome tiver sido alterado
            cat.slug = gerar_slug_unico(
                Categoria,
                cat,
                campo_origem="nome",
                campo_slug="slug"
            )

            cat.save()

            messages.success(
                request,
                f"Categoria '{cat.nome}' atualizada com sucesso!"
            )
            return redirect("lista_categorias")

        # Exibe mensagens com erros de validação
        for campo, erros in form.errors.items():
            for erro in erros:
                messages.error(request, f"{campo.capitalize()}: {erro}")
    else:
        form = CategoriaForm(instance=categoria)

    context = {
        "form": form,
        "categoria": categoria,
    }
    return render(request, "admin/editar_categoria.html", context)


def excluir_categoria(request, codigo):
    categoria = get_object_or_404(Categoria, pk=codigo)
    nome = categoria.nome

    try:
        categoria.delete()
        messages.success(
            request,
            f"A categoria '{nome}' foi excluída com sucesso."
        )
    except ProtectedError:
        messages.error(
            request,
            f"Não é possível excluir a categoria '{nome}', pois existem itens vinculados a ela. "
            "Realoque ou remova os itens antes de tentar novamente, ou desative a categoria."
        )

    return redirect("lista_categorias")

def view_categoria(request, codigo):
    categoria = get_object_or_404(Categoria, pk=codigo)
    return render(request, "admin/detalhes_categoria.html", {"categoria": categoria})


def lista_contatos(request):
    termo_busca = request.GET.get("q", "").strip()
    contatos_query = Contato.objects.all().order_by("-data")

    if termo_busca:
        contatos_query = contatos_query.filter(
            Q(nome__icontains=termo_busca) |
            Q(email__icontains=termo_busca) |
            Q(assunto__icontains=termo_busca) |
            Q(mensagem__icontains=termo_busca)
        )

    # Paginação: 10 mensagens por página
    paginator = Paginator(contatos_query, 10)
    pagina = request.GET.get("page", 1)

    try:
        contatos_paginados = paginator.page(pagina)
    except PageNotAnInteger:
        contatos_paginados = paginator.page(1)
    except EmptyPage:
        contatos_paginados = paginator.page(paginator.num_pages)

    context = {
        "contatos": contatos_paginados,
        "q": termo_busca,
    }
    return render(request, "admin/contatos.html", context)


def view_contato(request, pk):
    contato = get_object_or_404(Contato, pk=pk)
    return render(request, "admin/detalhes_contato.html", {"contato": contato})


def apagar_contato(request, pk):
    contato = get_object_or_404(Contato, pk=pk)
    nome = contato.nome or "Contato anônimo"
    contato.delete()
    messages.success(request, f"Mensagem de '{nome}' excluída com sucesso.")
    return redirect("lista_contatos")

@login_required
def novo_usuario(request):
    # Restringe a criação de usuários a administradores
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Acesso não autorizado para cadastrar novos usuários.")
        return redirecionar_por_perfil(request.user)

    if request.method == "POST":
        form = NovoUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request,
                f"Usuário '{usuario.nome or usuario.email}' cadastrado com sucesso!"
            )
            return redirect("lista_usuarios")
        else:
            messages.error(request, "Não foi possível cadastrar o usuário. Corrija os erros apontados.")
    else:
        form = NovoUsuarioForm()

    context = {
        "form": form,
        "instituicoes": Instituicao.objects.filter(ativo=True).order_by("nome"),
        "salas": Sala.objects.all().order_by("numero"),
        "tipos_usuario": Perfil.TipoUsuario.choices,
    }
    return render(request, "admin/novo_usuario.html", context)

@login_required
def lista_usuarios(request):
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Acesso restrito a administradores.")
        return redirect("usuario_home")

    termo_busca = request.GET.get("q", "").strip()
    usuarios_query = Perfil.objects.all().order_by("-date_joined")

    if termo_busca:
        digitos_cpf = apenas_digitos(termo_busca)
        filtro = (
            Q(nome__icontains=termo_busca) |
            Q(email__icontains=termo_busca) |
            Q(username__icontains=termo_busca)
        )
        if digitos_cpf:
            filtro |= Q(cpf__icontains=digitos_cpf)
        
        usuarios_query = usuarios_query.filter(filtro)

    # 10 usuários por página
    paginator = Paginator(usuarios_query, 10)
    pagina = request.GET.get("page", 1)

    try:
        usuarios_paginados = paginator.page(pagina)
    except PageNotAnInteger:
        usuarios_paginados = paginator.page(1)
    except EmptyPage:
        usuarios_paginados = paginator.page(paginator.num_pages)

    context = {
        "usuarios": usuarios_paginados,
        "q": termo_busca,
    }
    return render(request, "admin/usuarios.html", context)


@login_required
def alternar_status_usuario(request, pk):
    """
    Alterna o status entre Ativo e Inativo.
    Impede que o próprio administrador autenticado desative sua conta.
    """
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Permissão negada.")
        return redirect("usuario_home")

    usuario = get_object_or_404(Perfil, pk=pk)

    if usuario == request.user:
        messages.warning(request, "Você não pode desativar seu próprio usuário logado.")
        return redirect("lista_usuarios")

    # Inverte os status (tanto ativo de negócio quanto is_active do Django Auth)
    novo_status = not usuario.ativo
    usuario.ativo = novo_status
    usuario.is_active = novo_status
    usuario.save(update_fields=["ativo", "is_active"])

    status_str = "ativado" if novo_status else "desativado"
    messages.success(request, f"O usuário '{usuario.nome or usuario.email}' foi {status_str} com sucesso.")
    return redirect("lista_usuarios")


@login_required
def ativar_usuario(request, pk):
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Permissão negada.")
        return redirect("usuario_home")

    usuario = get_object_or_404(Perfil, pk=pk)
    usuario.ativo = True
    usuario.is_active = True
    usuario.save(update_fields=["ativo", "is_active"])
    messages.success(request, f"Usuário '{usuario.nome or usuario.email}' ativado com sucesso.")
    return redirect("lista_usuarios")


@login_required
def desativar_usuario(request, pk):
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Permissão negada.")
        return redirect("usuario_home")

    usuario = get_object_or_404(Perfil, pk=pk)
    if usuario == request.user:
        messages.warning(request, "Você não pode desativar a sua própria conta.")
        return redirect("lista_usuarios")

    usuario.ativo = False
    usuario.is_active = False
    usuario.save(update_fields=["ativo", "is_active"])
    messages.warning(request, f"Usuário '{usuario.nome or usuario.email}' desativado.")
    return redirect("lista_usuarios")


@login_required
def excluir_usuario(request, pk):
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Permissão negada.")
        return redirect("usuario_home")

    usuario = get_object_or_404(Perfil, pk=pk)
    if usuario == request.user:
        messages.error(request, "Não é permitido excluir o usuário atualmente autenticado.")
        return redirect("lista_usuarios")

    nome = usuario.nome or usuario.email
    usuario.delete()
    messages.success(request, f"Conta de '{nome}' excluída definitivamente.")
    return redirect("lista_usuarios")


@login_required
def visualizar_usuario(request, pk):
    usuario = get_object_or_404(Perfil, pk=pk)
    return render(request, "admin/detalhes_usuario.html", {"usuario": usuario})


@login_required
def lista_salas(request):
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Acesso restrito a administradores.")
        return redirect("usuario_home")

    termo_busca = request.GET.get("q", "").strip()
    salas_query = Sala.objects.all().order_by("predio", "numero")

    if termo_busca:
        filtro = (
            Q(numero__icontains=termo_busca) |
            Q(predio__icontains=termo_busca) |
            Q(andar__icontains=termo_busca)
        )
        # Se Sala tiver o campo 'codigo'
        if hasattr(Sala, "codigo"):
            filtro |= Q(codigo__icontains=termo_busca)

        salas_query = salas_query.filter(filtro)

    paginator = Paginator(salas_query, 10)
    pagina = request.GET.get("page", 1)

    try:
        salas_paginadas = paginator.page(pagina)
    except PageNotAnInteger:
        salas_paginadas = paginator.page(1)
    except EmptyPage:
        salas_paginadas = paginator.page(paginator.num_pages)

    context = {
        "salas": salas_paginadas,
        "q": termo_busca,
    }
    return render(request, "admin/salas.html", context)


@login_required
def nova_sala(request):
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Permissão negada.")
        return redirect("usuario_home")

    if request.method == "POST":
        form = SalaForm(request.POST)
        if form.is_valid():
            sala = form.save()
            messages.success(request, f"Sala {sala.numero} ({sala.predio}) cadastrada com sucesso!")
            return redirect("lista_salas")
        messages.error(request, "Erro ao cadastrar sala. Verifique os dados informados.")
    else:
        form = SalaForm(initial={"ativa": True})

    return render(request, "admin/nova_sala.html", {"form": form, "acao": "Nova Sala"})


@login_required
def detalhes_sala(request, codigo):
    # Se a PK de Sala for 'codigo', usa-se pk=codigo; caso contrário, use id=codigo
    sala = get_object_or_404(Sala, pk=codigo)
    
    # Servidores vinculados a esta sala
    servidores = Perfil.objects.filter(sala=sala, tipo=Perfil.TipoUsuario.SERVIDOR)

    return render(request, "admin/detalhes_sala.html", {
        "sala": sala,
        "servidores": servidores,
    })


@login_required
def editar_sala(request, codigo):
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Permissão negada.")
        return redirect("usuario_home")

    sala = get_object_or_404(Sala, pk=codigo)

    if request.method == "POST":
        form = SalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            messages.success(request, f"Sala {sala.numero} atualizada com sucesso!")
            return redirect("lista_salas")
        messages.error(request, "Não foi possível atualizar a sala. Verifique os campos.")
    else:
        form = SalaForm(instance=sala)

    return render(request, "admin/editar_sala.html", {
        "form": form,
        "sala": sala,
        "acao": "Editar Sala",
    })


@login_required
def alternar_status_sala(request, codigo):
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Permissão negada.")
        return redirect("usuario_home")

    sala = get_object_or_404(Sala, pk=codigo)
    # Suporta tanto o campo 'ativa' quanto 'ativo'
    campo_status = "ativa" if hasattr(sala, "ativa") else "ativo"
    status_atual = getattr(sala, campo_status, True)
    setattr(sala, campo_status, not status_atual)
    sala.save(update_fields=[campo_status])

    novo_status_str = "ativada" if getattr(sala, campo_status) else "desativada"
    messages.success(request, f"A Sala {sala.numero} foi {novo_status_str} com sucesso.")
    return redirect("lista_salas")


@login_required
def excluir_sala(request, codigo):
    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, "Permissão negada.")
        return redirect("usuario_home")

    sala = get_object_or_404(Sala, pk=codigo)
    nome_sala = f"Sala {sala.numero} - {sala.predio}"

    try:
        sala.delete()
        messages.success(request, f"{nome_sala} excluída definitivamente.")
    except ProtectedError:
        messages.error(
            request,
            f"Não é possível excluir a {nome_sala}, pois existem itens ou servidores vinculados a ela. "
            "Remova ou transfira os vínculos antes de excluir, ou apenas desative a sala."
        )

    return redirect("lista_salas")


@login_required
def lista_itens(request):
    termo_busca = request.GET.get("q", "").strip()
    status_filtro = request.GET.get("status", "").strip()
    itens_query = Item.objects.select_related("categoria", "instituicao", "local").order_by("-data_registro")

    if termo_busca:
        itens_query = itens_query.filter(
            Q(nome__icontains=termo_busca) |
            Q(codigo__iexact=termo_busca) |
            Q(marca_ou_modelo__icontains=termo_busca) |
            Q(descricao__icontains=termo_busca) |
            Q(cor__icontains=termo_busca)
        )

    if status_filtro and status_filtro.isdigit():
        itens_query = itens_query.filter(status=int(status_filtro))

    paginator = Paginator(itens_query, 10)
    pagina = request.GET.get("page", 1)

    try:
        itens_paginados = paginator.page(pagina)
    except PageNotAnInteger:
        itens_paginados = paginator.page(1)
    except EmptyPage:
        itens_paginados = paginator.page(paginator.num_pages)

    context = {
        "itens": itens_paginados,
        "q": termo_busca,
        "status_filtro": status_filtro,
        "status_choices": Item.StatusItem.choices,
    }
    return render(request, "admin/itens.html", context)


@login_required
def detalhes_item(request, uuid):
    item = get_object_or_404(Item.objects.select_related("categoria", "instituicao", "local", "local_guardado", "usuario_registro", "dono"), uuid=uuid)
    reivindicacoes = item.reivindicacoes.select_related("autor").order_by("-data")
    return render(request, "admin/detalhes_item.html", {"item": item, "reivindicacoes": reivindicacoes})


@login_required
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

    return render(request, "admin/editar_item.html", {"form": form, "item": item})


@login_required
def apagar_item(request, uuid):
    item = get_object_or_404(Item, uuid=uuid)
    identificador = str(item)

    try:
        item.delete()
        messages.success(request, f"{identificador} excluído com sucesso.")
    except ProtectedError:
        messages.error(
            request,
            f"Não é possível excluir o {identificador}, pois há vínculos protegidos associados a ele."
        )

    return redirect("lista_itens")


@login_required
def lista_reivindicacoes(request):
    termo_busca = request.GET.get("q", "").strip()
    status_filtro = request.GET.get("status", "").strip()
    reivindicacoes_query = Reivindicacao.objects.select_related("autor", "item", "instituicao").order_by("-data")

    if termo_busca:
        reivindicacoes_query = reivindicacoes_query.filter(
            Q(protocolo__icontains=termo_busca) |
            Q(autor__nome__icontains=termo_busca) |
            Q(autor__email__icontains=termo_busca) |
            Q(item__nome__icontains=termo_busca) |
            Q(item__codigo__iexact=termo_busca) |
            Q(pedido__icontains=termo_busca)
        )

    if status_filtro and status_filtro.isdigit():
        reivindicacoes_query = reivindicacoes_query.filter(status=int(status_filtro))

    paginator = Paginator(reivindicacoes_query, 10)
    pagina = request.GET.get("page", 1)

    try:
        reivindicacoes_paginadas = paginator.page(pagina)
    except PageNotAnInteger:
        reivindicacoes_paginadas = paginator.page(1)
    except EmptyPage:
        reivindicacoes_paginadas = paginator.page(paginator.num_pages)

    context = {
        "reivindicacoes": reivindicacoes_paginadas,
        "q": termo_busca,
        "status_filtro": status_filtro,
        "status_choices": Reivindicacao.StatusReivindicacao.choices,
    }
    return render(request, "admin/reivindicacoes.html", context)


@login_required
def detalhes_reivindicacao(request, protocolo):
    reivindicacao = get_object_or_404(
        Reivindicacao.objects.select_related(
            "autor", "item", "instituicao", "responsavel_admin", "local_devolucao"
        ),
        protocolo=protocolo
    )
    return render(request, "admin/detalhes_reivindicacao.html", {"reivindicacao": reivindicacao})


@login_required
def atualizar_reivindicacao(request, protocolo):
    reivindicacao = get_object_or_404(Reivindicacao, protocolo=protocolo)

    if request.method == "POST":
        form = ReivindicacaoUpdateForm(request.POST, instance=reivindicacao)
        if form.is_valid():
            reiv = form.save(commit=False)

            # Atribui o administrador logado caso o campo não tenha sido selecionado manualmente
            if not reiv.responsavel_admin and request.user.tipo == Perfil.TipoUsuario.ADMINISTRADOR:
                reiv.responsavel_admin = request.user

            # Se a reivindicação for concluída/aprovada, sincroniza o status do item correspondente
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
        request,
        "admin/editar_reivindicacao.html",
        {"form": form, "reivindicacao": reivindicacao}
    )


@login_required
def apagar_reivindicacao(request, protocolo):
    reivindicacao = get_object_or_404(Reivindicacao, protocolo=protocolo)
    num_protocolo = reivindicacao.protocolo
    reivindicacao.delete()
    messages.success(request, f"Reivindicação #{num_protocolo} removida com sucesso.")
    return redirect("lista_reivindicacoes")    



@login_required
def meu_perfil(request):
    return render(request, "admin/meu_perfil.html", {"usuario": request.user})


@login_required
def editar_meu_perfil(request):
    usuario = request.user
    if request.method == "POST":
        form = EditarMeuPerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            usuario_salvo = form.save()

            # Sincroniza os novos dados com a sessão do usuário
            request.session["username"] = usuario_salvo.username
            request.session["primeiro_nome"] = usuario_salvo.primeiro_nome
            request.session["foto_url"] = usuario_salvo.foto.url if usuario_salvo.foto else None

            messages.success(request, "Seus dados foram atualizados com sucesso!")
            return redirect("meu_perfil")
        messages.error(request, "Erro ao atualizar seus dados. Verifique os campos.")
    else:
        form = EditarMeuPerfilForm(instance=usuario)

    return render(request, "admin/editar_perfil.html", {"form": form, "usuario": usuario})



@login_required
def trocar_minha_senha(request):
    if request.method == "POST":
        form = TrocarMinhaSenhaForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Impede que o usuário seja desconectado após alterar a credencial
            update_session_auth_hash(request, user)
            messages.success(request, "Sua senha foi alterada com sucesso!")
            return redirect("meu_perfil")
        messages.error(request, "Não foi possível alterar sua senha. Confira os requisitos abaixo.")
    else:
        form = TrocarMinhaSenhaForm(user=request.user)

    return render(request, "admin/trocar_senha.html", {"form": form})