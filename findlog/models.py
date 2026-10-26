import uuid
import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from datetime import date

from .utils import (
    apenas_digitos,
    formatar_cnpj,
    formatar_telefone,
    remover_acentos,
    gerar_slug_unico,
    validar_cnpj,
    validar_cpf,
    gerar_codigo_aleatorio,
    formatar_cpf,
)


class Instituicao(models.Model):
    cnpj = models.CharField(
        "CNPJ da Instituição",
        max_length=14,
        primary_key=True,
        validators=[validar_cnpj]
    )
    nome = models.CharField("Nome da Instituição", max_length=255)
    endereco = models.CharField(
        "Endereço da Instituição",
        max_length=100,
        help_text="Digite o endereço de onde a plataforma será utilizada"
    )
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("E-mail")
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField("Data de cadastro", auto_now_add=True)

    def _sanitizar_campos(self):
        self.cnpj = apenas_digitos(self.cnpj)
        self.telefone = apenas_digitos(self.telefone)

    def clean(self):
        super().clean()
        self._sanitizar_campos()

    def save(self, *args, **kwargs):
        self._sanitizar_campos()
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def cnpj_formatado(self):
        return formatar_cnpj(self.cnpj)

    @property
    def telefone_formatado(self):
        return formatar_telefone(self.telefone)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Instituição"
        verbose_name_plural = "Instituições"


class Categoria(models.Model):
    codigo = models.CharField("Código", max_length=4, primary_key=True, editable=False, blank=True)
    nome = models.CharField("Nome", max_length=255)
    descricao = models.TextField("Descrição", blank=True)
    ativa = models.BooleanField(default=True)
    slug = models.SlugField("Slug", max_length=150, unique=True, editable=False, blank=True)

    def _gerar_codigo(self):
        nome_limpo = slugify(self.nome).replace("-", "").upper()
        prefixo = nome_limpo[:2] if len(nome_limpo) >= 2 else (nome_limpo + "X")[:2]

        for _ in range(200):
            numeros = "".join(random.choices(string.digits, k=2))
            codigo_candidato = f"{prefixo}{numeros}"

            qs = Categoria.objects.filter(codigo=codigo_candidato)
            if self.pk:
                qs = qs.exclude(pk=self.pk)

            if not qs.exists():
                return codigo_candidato

        # Fallback alfanumérico se o prefixo esgotar
        while True:
            candidato = gerar_codigo_aleatorio(tamanho=4)
            if not Categoria.objects.filter(codigo=candidato).exists():
                return candidato

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self._gerar_codigo()

        if not self.slug:
            self.slug = gerar_slug_unico(Categoria, self, campo_origem='nome', campo_slug='slug')

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]


class Sala(models.Model):
    codigo = models.CharField("Código do local", unique=True, max_length=10, blank=True, editable=False)
    instituicao = models.ForeignKey(
        Instituicao,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Instituição",
        related_name="salas"
    )
    predio = models.CharField("Prédio", max_length=5)
    andar = models.CharField("Andar", max_length=5)
    nome = models.CharField("Nome do local", max_length=50, default="Sala do IFPI")
    telefone = models.CharField("Telefone do local", max_length=15, blank=True, default="")
    descricao = models.TextField("Descrição do local", blank=True, default="")
    sala_de_aula = models.BooleanField("Sala de aula?", default=False)
    laboratorio = models.BooleanField("Laboratório?", default=False)
    ativa = models.BooleanField("Ativo", default=True)

    def _sanitizar_campos(self):
        self.telefone = apenas_digitos(self.telefone)

    @property
    def telefone_formatado(self):
        return formatar_telefone(self.telefone)

    def gerar_codigo(self):
        nome_sem_acento = remover_acentos(self.nome or "")
        letras = "".join(letra for letra in nome_sem_acento.upper() if letra.isalpha())
        prefixo = letras[:3].ljust(3, "X")

        qs = type(self).objects.filter(codigo__startswith=prefixo)
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        codigos_existentes = set(qs.values_list("codigo", flat=True))

        for numero in range(1000):
            codigo_candidato = f"{prefixo}{numero:03d}"
            if codigo_candidato not in codigos_existentes:
                return codigo_candidato

        raise ValidationError(f"Capacidade esgotada para o prefixo '{prefixo}'.")

    def clean(self):
        super().clean()
        self._sanitizar_campos()

    def save(self, *args, **kwargs):
        self._sanitizar_campos()
        if not self.codigo:
            self.codigo = self.gerar_codigo()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome}" if self.codigo else self.nome

    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
        ordering = ["predio", "andar", "nome"]


class Perfil(AbstractUser):
    class TipoUsuario(models.IntegerChoices):
        ADMINISTRADOR = 1, "Administrador"
        USUARIO = 2, "Usuário"
        SERVIDOR = 3, "Servidor"

    username = models.CharField("Username", max_length=100, unique=True)
    nome = models.CharField("Nome completo", max_length=100, blank=True, null=True)
    instituicao = models.ManyToManyField(
        Instituicao,
        through='VinculoInstituicao',
        related_name="perfis"
    )
    email = models.EmailField("Email", unique=True)
    telefone = models.CharField("Telefone", max_length=15, blank=True, null=True)
    data_nascimento = models.DateField("Data de Nascimento", null=True, blank=True)
    cpf = models.CharField("CPF", max_length=11, unique=True, validators=[validar_cpf])
    foto = models.ImageField("Foto de Perfil", upload_to="usuarios/fotos/", blank=True, null=True)
    tipo = models.PositiveSmallIntegerField("Tipo de Usuário", choices=TipoUsuario.choices, default=TipoUsuario.USUARIO)
    codigo = models.CharField("Matrícula", max_length=20, blank=True, null=True)
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, blank=True, null=True, help_text="Obrigatório apenas para servidores")
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField("Ativo", default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def _sanitizar_campos(self):
        self.cpf = apenas_digitos(self.cpf)
        self.telefone = apenas_digitos(self.telefone)

    def gerar_username(self):
        base_username = self.email.split("@")[0] if self.email and "@" in self.email else (self.email or "usuario")
        while True:
            numeros = "".join(random.choices(string.digits, k=4))
            candidato = f"{base_username}{numeros}"
            if not Perfil.objects.filter(username=candidato).exists():
                return candidato

    @property
    def primeiro_nome(self):
        return self.nome.split()[0] if self.nome else ""

    @property
    def telefone_formatado(self):
        return formatar_telefone(self.telefone)

    @property
    def cpf_formatado(self) -> str:
        """Máscara de exibição: XXX.XXX.XXX-XX"""
        return formatar_cpf(self.cpf)    

    @property
    def idade(self) -> int | None:
        """Calcula a idade exata com base na data de nascimento e no dia atual."""
        if not self.data_nascimento:
            return None
        hoje = date.today()
        fez_aniversario_este_ano = (hoje.month, hoje.day) >= (self.data_nascimento.month, self.data_nascimento.day)
        return hoje.year - self.data_nascimento.year - (0 if fez_aniversario_este_ano else 1)    

    def clean(self):
        super().clean()
        self._sanitizar_campos()

    def save(self, *args, **kwargs):
        self._sanitizar_campos()
        if not self.username:
            self.username = self.gerar_username()  # Corrigido: chamada do método com ()

        # 1. Se veio do createsuperuser (is_superuser=True), garante o tipo ADMINISTRADOR
        if self.is_superuser:
            self.tipo = self.TipoUsuario.ADMINISTRADOR
            self.is_staff = True

        # 2. Se foi marcado como ADMINISTRADOR pelo painel/form, garante os privilégios
        elif self.tipo == self.TipoUsuario.ADMINISTRADOR:
            self.is_superuser = True
            self.is_staff = True

        # 3. Caso contrário (Usuário Comum ou Servidor), remove privilégios elevados
        else:
            self.is_superuser = False
            self.is_staff = False  
                
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome or self.email

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"


class VinculoInstituicao(models.Model):
    """Modelo intermediário para ManyToMany entre Perfil e Instituicao."""
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    instituicao = models.ForeignKey(Instituicao, on_delete=models.CASCADE)
    data_vinculo = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Vínculo com Instituição"
        verbose_name_plural = "Vínculos com Instituições"
        unique_together = ("perfil", "instituicao")


class Item(models.Model):
    class StatusItem(models.IntegerChoices):
        PERDIDO = 1, "Perdido"
        ENCONTRADO = 2, "Encontrado"
        DEVOLVIDO = 3, "Devolvido"
        OUTRO = 4, "Outro"

    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Categoria")
    instituicao = models.ForeignKey(Instituicao, verbose_name="Instituição onde foi encontrado", on_delete=models.CASCADE)
    nome = models.CharField("Nome do item", max_length=100, blank=True, null=True)
    usuario_registro = models.ForeignKey(
        Perfil,
        on_delete=models.SET_NULL,
        related_name='itens_registrados',
        verbose_name="Usuário responsável",
        blank=True,
        null=True
    )
    dono = models.ForeignKey(
        Perfil,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='itens_recuperados',
        verbose_name="Dono do item"
    )
    tamanho = models.CharField("Tamanho do item", max_length=20, blank=True, null=True)
    cor = models.CharField("Cor do item", max_length=20, blank=True, null=True)
    material = models.CharField("Material do item", max_length=50, blank=True, null=True)
    codigo = models.CharField("Código do item", max_length=10, unique=True, blank=True)
    marca_ou_modelo = models.CharField("Marca ou modelo do item", max_length=50, blank=True, null=True)
    local = models.ForeignKey(Sala, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Local que foi encontrado")
    local_guardado = models.ForeignKey(Sala, on_delete=models.SET_NULL, blank=True, null=True, related_name="itens_guardados", verbose_name="Local guardado")
    data_registro = models.DateTimeField("Data de registro", auto_now_add=True)
    data_devolucao = models.DateTimeField("Data de devolução", blank=True, null=True)
    foto = models.ImageField("Foto do item", upload_to="itens/fotos/", blank=True, null=True)
    descricao = models.TextField("Descrição do item", blank=True, null=True)
    status = models.PositiveSmallIntegerField("Status", choices=StatusItem.choices, default=StatusItem.PERDIDO)

    def save(self, *args, **kwargs):
        if not self.codigo:
            codigo = gerar_codigo_aleatorio(tamanho=8)
            while Item.objects.filter(codigo=codigo).exists():
                codigo = gerar_codigo_aleatorio(tamanho=8)
            self.codigo = codigo

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} ({self.codigo})" if self.nome else f"Item {self.codigo}"

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"


class Reivindicacao(models.Model):
    class StatusReivindicacao(models.IntegerChoices):
        PENDENTE = 1, "Pendente"
        EM_ANALISE = 2, "Em análise"
        APROVADA = 3, "Aprovada"
        REJEITADA = 4, "Rejeitada"
        CONCLUIDA = 5, "Concluída"

    protocolo = models.BigAutoField(primary_key=True)
    data = models.DateTimeField("Data da solicitação", auto_now_add=True)
    autor = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="reivindicacoes")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="reivindicacoes")
    instituicao = models.ForeignKey(Instituicao, on_delete=models.CASCADE, related_name="reivindicacoes")
    status = models.PositiveSmallIntegerField("Status", choices=StatusReivindicacao.choices, default=StatusReivindicacao.PENDENTE)
    resposta_admin = models.TextField("Resposta à reivindicação", blank=True)
    pedido = models.TextField("Descrição da Reivindicação")
    anexos = models.FileField(upload_to="reivindicacoes/anexos/", blank=True, null=True)
    responsavel_admin = models.ForeignKey(Perfil, on_delete=models.SET_NULL, null=True, blank=True, related_name="reivindicacoes_atendidas")
    local_devolucao = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True, related_name="reivindicacoes")
    data_devolucao = models.DateTimeField("Data de devolução", null=True, blank=True)

    def __str__(self):
        return f"Reivindicação #{self.protocolo}"

    class Meta:
        verbose_name = "Reivindicação"
        verbose_name_plural = "Reivindicações"
        ordering = ["-data"]  # Corrigido de data_criacao para data


class Contato(models.Model):
    class Assuntos(models.TextChoices):
        DUVIDA = "DUVIDA", "Dúvida"
        SUGESTAO = "SUGESTAO", "Sugestão"
        RECLAMACAO = "RECLAMACAO", "Reclamação"
        ELOGIO = "ELOGIO", "Elogio"
        ORCAMENTO = "ORCAMENTO", "Orçamento"
        PARCERIA = "PARCERIA", "Parceria"
        OUTRO = "OUTRO", "Outro"


    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nome = models.CharField("Nome", max_length=100, blank=True, null=True)
    email = models.EmailField("Email", max_length=100, blank=True, null=True)
    assunto = models.CharField("Assunto", max_length=20, choices=Assuntos.choices)
    telefone = models.CharField("Telefone", max_length=15, null=True, blank=True)
    mensagem = models.TextField("Mensagem", blank=True, null=True)
    data = models.DateTimeField(auto_now_add=True)
    ip_contato = models.GenericIPAddressField("IP de Origem", null=True, blank=True)

    def _sanitizar_campos(self):
        self.telefone = apenas_digitos(self.telefone)

    @property
    def telefone_formatado(self):
        telefone = self.telefone
        return formatar_telefone(telefone)

    def save(self, *args, **kwargs):
        self._sanitizar_campos()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome or "Contato sem nome"

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"
        ordering = ["-data"]