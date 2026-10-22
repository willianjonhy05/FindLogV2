import re
import string
import random
import unicodedata
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from django.shortcuts import redirect


def apenas_digitos(valor: str) -> str:
    """Remove qualquer caractere não numérico da string."""
    if not valor:
        return ""
    return re.sub(r'\D', '', str(valor))


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
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )


def gerar_slug_unico(model_class, instancia, campo_origem='nome', campo_slug='slug') -> str:
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
    Exemplo de validador de CNPJ (mantenha sua implementação real aqui).
    """
    cnpj = apenas_digitos(valor)
    if len(cnpj) != 14:
        raise ValidationError("CNPJ inválido: deve conter 14 dígitos.")


def gerar_codigo_aleatorio(tamanho: int = 8, caracteres: str = string.ascii_uppercase + string.digits) -> str:
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
        return redirect("admin:index")

    # 2. Administrador comum vai para a dashboard personalizada
    if usuario.tipo == Perfil.TipoUsuario.ADMINISTRADOR:
        return redirect("dashboard_admin")
    elif usuario.tipo == Perfil.TipoUsuario.SERVIDOR:
        return redirect("servidor_painel")

    return redirect("usuario_home")