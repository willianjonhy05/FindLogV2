import re
import string
import random
import secrets
import unicodedata
import base64
from io import BytesIO
import qrcode
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.shortcuts import redirect
from django.http import Http404
from django.contrib import messages
from django.core.paginator import Paginator


def apenas_digitos(valor: str) -> str:
    """Remove qualquer caractere não numérico da string."""
    if not valor:
        return ""
    return re.sub(r"\D", "", str(valor))

def higienizar_dados_post(post_data, campos=("cpf", "telefone", "cnpj")):
    """Retorna uma cópia mutável do QueryDict mantendo apenas dígitos nos campos informados."""
    dados = post_data.copy()
    for campo in campos:
        if dados.get(campo):
            dados[campo] = apenas_digitos(dados[campo])
    return dados    


def verificar_acesso_admin(request, mensagem="Permissão negada.", destino="usuario_home"):
    """
    Valida se o usuário possui papel de Administrador ou Superusuário.
    Retorna um HttpResponseRedirect em caso de bloqueio, ou None se autorizado.
    """
    from .models import Perfil

    if request.user.tipo != Perfil.TipoUsuario.ADMINISTRADOR and not request.user.is_superuser:
        messages.error(request, mensagem)
        return redirect(destino)
    return None

def paginar_queryset(request, queryset, por_pagina=10):
    """Pagina qualquer QuerySet usando get_page() (trata páginas inválidas ou vazias)."""
    paginator = Paginator(queryset, por_pagina)
    return paginator.get_page(request.GET.get("page"))


def formatar_cnpj(cnpj: str) -> str:
    """Formata CNPJ no padrão XX.XXX.XXX/XXXX-XX."""
    digitos = apenas_digitos(cnpj)
    if len(digitos) == 14:
        return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
    return cnpj or ""


def formatar_telefone(telefone: str) -> str:
    """Formata telefone para fixo (XX) XXXX-XXXX ou celular (XX) XXXXX-XXXX."""
    digitos = apenas_digitos(telefone)
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    elif len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return telefone or ""


def remover_acentos(texto: str) -> str:
    """Remove caracteres com acento de uma string."""
    if not texto:
        return ""
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def gerar_slug_unico(model_class, instancia, campo_origem="nome", campo_slug="slug") -> str:
    """Gera um slug único para instâncias de um model."""
    valor_origem = getattr(instancia, campo_origem, "") or "item"
    slug_base = slugify(valor_origem) or "item"
    slug_candidato = slug_base
    contador = 2

    qs = model_class.objects.filter(**{campo_slug: slug_candidato})
    if instancia.pk:
        qs = qs.exclude(pk=instancia.pk)

    while qs.exists():
        slug_candidato = f"{slug_base}-{contador}"
        qs = model_class.objects.filter(**{campo_slug: slug_candidato})
        if instancia.pk:
            qs = qs.exclude(pk=instancia.pk)
        contador += 1

    return slug_candidato


def validar_cnpj(valor):
    """
    Valida um CNPJ brasileiro (aceitando formatado ou apenas dígitos)
    verificando tamanho, sequências repetidas e dígitos verificadores.
    Lança ValidationError caso seja inválido.
    """
    if not valor:
        return

    cnpj = apenas_digitos(valor)

    if len(cnpj) != 14:
        raise ValidationError("CNPJ inválido: deve conter 14 dígitos.")

    # Bloqueia sequências inválidas de dígitos iguais (ex: 11.111.111/1111-11)
    if len(set(cnpj)) == 1:
        raise ValidationError("CNPJ inválido.")

    def _calcular_digito(fatia_cnpj, pesos):
        soma = sum(int(digito) * peso for digito, peso in zip(fatia_cnpj, pesos))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    pesos_primeiro_digito = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos_segundo_digito = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    digito_1 = _calcular_digito(cnpj[:12], pesos_primeiro_digito)
    digito_2 = _calcular_digito(cnpj[:13], pesos_segundo_digito)

    if cnpj[-2:] != f"{digito_1}{digito_2}":
        raise ValidationError("CNPJ inválido: dígitos verificadores não conferem.")


def gerar_codigo_aleatorio(
    tamanho: int = 8, caracteres: str = string.ascii_uppercase + string.digits
) -> str:
    """Gera uma string aleatória com o comprimento especificado."""
    return "".join(random.choices(caracteres, k=tamanho))


def validar_cpf(valor: str) -> None:
    """
    Valida um CPF calculando os dois dígitos verificadores oficiais.
    Lança ValidationError se for inválido.
    """
    cpf = apenas_digitos(valor)

    # Verifica tamanho exato e rejeita sequências repetidas (ex: 111.111.111-11)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido: certifique-se de que possui 11 dígitos válidos.")

    # Validação do primeiro dígito verificador
    soma_1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto_1 = (soma_1 * 10) % 11
    digito_1 = 0 if resto_1 == 10 else resto_1

    if int(cpf[9]) != digito_1:
        raise ValidationError("CPF inválido: dígito verificador incorreto.")

    # Validação do segundo dígito verificador
    soma_2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto_2 = (soma_2 * 10) % 11
    digito_2 = 0 if resto_2 == 10 else resto_2

    if int(cpf[10]) != digito_2:
        raise ValidationError("CPF inválido: dígito verificador incorreto.")


def formatar_cpf(cpf: str) -> str:
    """Retorna o CPF no formato de máscara XXX.XXX.XXX-XX."""
    digitos = apenas_digitos(cpf)
    if len(digitos) == 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    return cpf or ""


def obter_ip_usuario(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def redirecionar_por_perfil(request, usuario):
    from .models import Perfil

    """
    Encaminha o usuário para o painel correspondente ao seu perfil,
    respeitando o parâmetro ?next= se existir.
    """
    next_url = request.GET.get("next")
    if next_url:
        return redirect(next_url)

    # 1. Superusuário vai direto para o Django Admin nativo
    if usuario.is_superuser:
        return redirect("dashboard_admin")

    # 2. Administrador comum vai para a dashboard personalizada
    if usuario.tipo == Perfil.TipoUsuario.ADMINISTRADOR:
        return redirect("dashboard_admin")
    elif usuario.tipo == Perfil.TipoUsuario.SERVIDOR:
        return redirect("servidor_painel")

    return redirect("usuario_feed")


def _obter_instituicao_do_servidor(request):
    """
    Função auxiliar para recuperar a instituição do servidor autenticado.
    Ajuste de acordo com o relacionamento do seu User (ex: request.user.servidor.instituicao).
    """
    try:
        return request.user.servidor.instituicao
    except AttributeError:
        return getattr(request.user, "instituicao", None)


def gerar_senha_provisoria(tamanho=10):
    """Gera uma senha segura com letras maiúsculas, minúsculas e dígitos."""
    caracteres = string.ascii_letters + string.digits + "@#$%"
    return "".join(secrets.choice(caracteres) for _ in range(tamanho))


def _obter_instituicao_por_token(token):
    from .models import Instituicao

    """Decodifica e valida o token assinado da instituição."""
    # Se quiser que o link expire em 30 dias, passe: max_age=60 * 60 * 24 * 30
    instituicao = Instituicao.obter_por_token(token, max_age=None)
    if not instituicao:
        raise Http404("Link de convite inválido ou expirado.")
    return instituicao


def gerar_qrcode_base64(texto, fill_color="#0B2347", back_color="#FFFFFF"):
    """
    Gera uma imagem PNG de QR Code codificada em Base64 (Data URI)
    pronta para ser renderizada em tags <img src="..."> e baixada.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(texto)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"


def exibir_erros_formulario(request, form):
    """Envia cada erro de validação do formulário como mensagem flash de erro."""
    for campo, erros in form.errors.items():
        prefixo = "" if campo == "__all__" else f"{campo.capitalize()}: "
        for erro in erros:
            messages.error(request, f"{prefixo}{erro}")    


def _obter_perfil_servidor(request):
    """Helper interno para validar se o usuário logado possui perfil de SERVIDOR."""
    from .models import Perfil

    perfil = request.user
    if not perfil.is_authenticated or perfil.tipo != Perfil.TipoUsuario.SERVIDOR:
        return None
    return perfil


def _obter_instituicao_servidor(request):
    """Retorna a instituição ativa da sessão validada contra o vínculo do servidor."""
    cnpj_sessao = request.session.get("instituicao_cnpj")
    if cnpj_sessao:
        inst = request.user.instituicao.filter(cnpj=cnpj_sessao, ativo=True).first()
        if inst:
            return inst
    return request.user.instituicao.filter(ativo=True).first()    