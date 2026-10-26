from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ServidorSalaForm, ServidorUpdateSalaForm
from .models import Perfil, Sala
from .decorators import servidor_required
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .utils import _obter_instituicao_do_servidor
from django.db.models import Q

def servidor_painel(request):
    return render(request, "servidor/index.html")

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

@login_required
def servidor_editar_sala(request, codigo):
    instituicao = _obter_instituicao_do_servidor(request)
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


@login_required
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

@login_required
@require_POST
def servidor_ativar_sala(request, codigo):
    instituicao = _obter_instituicao_do_servidor(request)
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
def servidor_detalhar_sala(request, codigo):
    instituicao = _obter_instituicao_do_servidor(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect('servidor_painel')

    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)

    context = {
        "sala": sala
    }

    return render(request, "serv/detalhar_sala.html", context)


@login_required
@require_POST
def servidor_desativar_sala(request, codigo):
    instituicao = _obter_instituicao_do_servidor(request)
    if not instituicao:
        messages.error(request, "Ação não permitida: vínculo institucional ausente.")
        return redirect('servidor_painel')

    # Só altera se a sala pertencer à mesma unidade
    sala = get_object_or_404(Sala, codigo=codigo, instituicao=instituicao)
    
    if sala.ativa:
        sala.ativa = False
        sala.save(update_fields=['ativa'])
        messages.warning(request, f'A sala "{sala.nome}" foi desativada.')
    else:
        messages.info(request, f'A sala "{sala.nome}" já se encontra inativa.')

    return redirect('servidor_listar_salas')


def listar_itens_por_sala(request):
    pass