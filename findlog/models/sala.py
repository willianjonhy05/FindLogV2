from django.db import models
from ..utils import apenas_digitos, formatar_telefone, remover_acentos
from django.core.exceptions import ValidationError
from .instituicao import Instituicao

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
    predio = models.CharField("Prédio", max_length=15)
    andar = models.CharField("Andar", max_length=15)
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
