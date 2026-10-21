from django.shortcuts import render, redirect
from django.contrib import messages
from findlog.forms import ContatoForm, LoginForm
from findlog.utils import obter_ip_usuario, redirecionar_por_perfil
from django.contrib.auth import login, logout



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
        return redirecionar_por_perfil(request.user)

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            usuario = form.user
            login(request, usuario)
            messages.success(request, f"Bem-vindo(a) de volta, {usuario.primeiro_nome}!")

            # Suporte ao redirecionamento por ?next=
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirecionar_por_perfil(usuario)
        else:
            messages.error(request, "Falha na autenticação. Verifique os dados.")
    else:
        form = LoginForm()

    return render(request, "public/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "Sua sessão foi encerrada com segurança.")
    return redirect("login")


