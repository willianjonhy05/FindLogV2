from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from findlog.forms import ContatoForm, LoginForm
from findlog.utils import obter_ip_usuario, redirecionar_por_perfil
from django.contrib.auth import login, logout
from findlog.models import Perfil, Instituicao
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST



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
        return redirecionar_por_perfil(request, request.user)

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            usuario = form.user
            login(request, usuario)

            # 1. Armazena dados essenciais do usuário na sessão
            request.session["username"] = usuario.username
            request.session["primeiro_nome"] = usuario.primeiro_nome
            request.session["foto_url"] = usuario.foto.url if usuario.foto else None

            messages.success(request, f"Bem-vindo(a) de volta, {usuario.primeiro_nome}!")

            # 2. Resolução da Instituição
            instituicoes_usuario = usuario.instituicao.filter(ativo=True)
            total_inst = instituicoes_usuario.count()

            # Administrador: pega a primeira instituição do sistema ou do próprio vínculo
            if usuario.tipo == Perfil.TipoUsuario.ADMINISTRADOR or usuario.is_superuser:
                primeira_inst = instituicoes_usuario.first() or Instituicao.objects.filter(ativo=True).first()
                if primeira_inst:
                    request.session["instituicao_cnpj"] = primeira_inst.cnpj
                    request.session["instituicao_nome"] = primeira_inst.nome
                return redirecionar_por_perfil(request, usuario)

            # Usuário Comum (2) ou Servidor (3)
            if total_inst > 1:
                # Encaminha para escolher qual instituição acessar
                return redirect("selecionar_instituicao")
            elif total_inst == 1:
                unica_inst = instituicoes_usuario.first()
                request.session["instituicao_cnpj"] = unica_inst.cnpj
                request.session["instituicao_nome"] = unica_inst.nome
                return redirecionar_por_perfil(request, usuario)
            else:
                request.session["instituicao_cnpj"] = None
                request.session["instituicao_nome"] = None
                return redirecionar_por_perfil(request, usuario)
        else:
            messages.error(request, "Falha na autenticação. Verifique os dados.")
    else:
        form = LoginForm()

    return render(request, "public/login.html", {"form": form})


@login_required
def selecionar_instituicao(request):
    """
    Permite escolher a instituição no login (quando houver mais de uma)
    ou trocar de instituição a qualquer momento.
    """
    usuario = request.user

    # Administrador pode escolher qualquer instituição ativa; demais apenas as que possuem vínculo
    if usuario.tipo == Perfil.TipoUsuario.ADMINISTRADOR or usuario.is_superuser:
        instituicoes = Instituicao.objects.filter(ativo=True)
    else:
        instituicoes = usuario.instituicao.filter(ativo=True)

    if request.method == "POST":
        cnpj_escolhido = request.POST.get("instituicao_cnpj")
        inst = get_object_or_404(instituicoes, cnpj=cnpj_escolhido)

        # Atualiza a instituição ativa na sessão
        request.session["instituicao_cnpj"] = inst.cnpj
        request.session["instituicao_nome"] = inst.nome
        messages.success(request, f"Instituição ativa alterada para: {inst.nome}")

        return redirecionar_por_perfil(request, usuario)

    context = {
        "instituicoes": instituicoes,
        "instituicao_atual": request.session.get("instituicao_cnpj"),
    }
    return render(request, "public/selecionar_instituicao.html", context)


def logout_view(request):
    logout(request)
    messages.info(request, "Sua sessão foi encerrada com segurança.")
    return redirect("login")
