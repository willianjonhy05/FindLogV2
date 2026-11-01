from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from findlog.forms import ContatoForm, LoginForm
from findlog.utils import obter_ip_usuario, redirecionar_por_perfil
from django.contrib.auth import login, logout
from findlog.models import Perfil, Instituicao
from django.contrib.auth.decorators import login_required




def index(request):
    if request.method == "POST":
        form_contato = ContatoForm(request.POST)

        if form_contato.is_valid():
            contato = form_contato.save(commit=False)
            contato.ip_contato = obter_ip_usuario(request)
            contato.save()

            messages.success(
                request,
                "Mensagem enviada com sucesso! Agradecemos pelo contato."
            )
            return redirect("home")

        messages.error(
            request,
            "Não foi possível enviar a mensagem. Verifique os campos e tente novamente."
        )
    else:
        form_contato = ContatoForm()

    return render(request,"public/index.html", {"form_contato": form_contato})

def login_view(request):
    if request.user.is_authenticated:
        if not getattr(request.user, "ativo", True) or not request.user.is_active:
            logout(request)
            return render(
                request,
                "403.html",
                {"mensagem": "Sua conta de usuário está desativada no sistema."},
                status=403,
            )
        return redirecionar_por_perfil(request, request.user)

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            usuario = form.user

            # Verificação de Perfil Ativo
            if not usuario.ativo or not usuario.is_active:
                return render(
                    request,
                    "403.html",
                    {
                        "mensagem": "Seu perfil está desativado. Entre em contato com a administração para reativar o acesso."
                    },
                    status=403,
                )

            login(request, usuario)

            # 1. Dados essenciais do usuário na sessão
            request.session["username"] = usuario.username
            request.session["primeiro_nome"] = usuario.primeiro_nome
            request.session["foto_url"] = usuario.foto.url if usuario.foto else None

            messages.success(
                request,
                f"Bem-vindo(a) de volta, {usuario.primeiro_nome or usuario.nome or usuario.username}!",
            )

            # 2. Resolução das Instituições
            is_admin = (
                usuario.tipo == Perfil.TipoUsuario.ADMINISTRADOR or usuario.is_superuser
            )

            if is_admin:
                instituicoes_disponiveis = Instituicao.objects.filter(ativo=True)
            else:
                instituicoes_disponiveis = usuario.instituicao.filter(ativo=True)

            total_inst = instituicoes_disponiveis.count()
            # Salva na sessão para controle do dropdown no template
            request.session["total_instituicoes"] = total_inst

            # 3. Regra de Redirecionamento
            if total_inst > 1:
                # Mais de uma: sempre escolhe primeiro
                return redirect("selecionar_instituicao")
            elif total_inst == 1:
                # Exatamente uma: fixa na sessão e entra direto
                unica_inst = instituicoes_disponiveis.first()
                request.session["instituicao_cnpj"] = unica_inst.cnpj
                request.session["instituicao_nome"] = unica_inst.nome
                return redirecionar_por_perfil(request, usuario)
            else:
                # Nenhuma instituição vinculada
                request.session["instituicao_cnpj"] = None
                request.session["instituicao_nome"] = None
                return redirecionar_por_perfil(request, usuario)
        else:
            messages.error(
                request, "Falha na autenticação. Verifique os dados informados."
            )
    else:
        form = LoginForm()

    return render(request, "public/login.html", {"form": form})


@login_required
def selecionar_instituicao(request):
    usuario = request.user

    if usuario.tipo == Perfil.TipoUsuario.ADMINISTRADOR or usuario.is_superuser:
        instituicoes = Instituicao.objects.filter(ativo=True)
    else:
        instituicoes = usuario.instituicao.filter(ativo=True)

    total_inst = instituicoes.count()
    request.session["total_instituicoes"] = total_inst

    # Se por acaso só tiver 1 instituição, fixa e já redireciona
    if total_inst == 1:
        inst = instituicoes.first()
        request.session["instituicao_cnpj"] = inst.cnpj
        request.session["instituicao_nome"] = inst.nome
        return redirecionar_por_perfil(request, usuario)

    if request.method == "POST":
        cnpj_escolhido = request.POST.get("instituicao_cnpj")
        inst = get_object_or_404(instituicoes, cnpj=cnpj_escolhido)

        request.session["instituicao_cnpj"] = inst.cnpj
        request.session["instituicao_nome"] = inst.nome
        messages.success(request, f"Instituição ativa alterada para: {inst.nome}")

        return redirecionar_por_perfil(request, usuario)

    context = {
        "instituicoes": instituicoes,
        "instituicao_atual": request.session.get("instituicao_cnpj"),
    }
    return render(request, "public/selecionar_instituicao.html", context)

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Sua sessão foi encerrada com segurança.")
    return redirect("login")
