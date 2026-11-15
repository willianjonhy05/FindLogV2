from django.db import models
from django.utils.text import slugify
from ..utils import gerar_slug_unico, gerar_codigo_aleatorio

import string
import random

class Categoria(models.Model):
    codigo = models.CharField("Código", max_length=6, primary_key=True, editable=False, blank=True)
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

