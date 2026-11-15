from django.db import models
from django.contrib.auth.models import AbstractUser
from ..utils import apenas_digitos, formatar_telefone, validar_cpf, formatar_cpf

from .instituicao import Instituicao
from .sala import Sala

from datetime import date
import random
import string

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

