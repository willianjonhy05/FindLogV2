from django.db import models
import uuid
from ..utils import (
    apenas_digitos,
    formatar_telefone,

)


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