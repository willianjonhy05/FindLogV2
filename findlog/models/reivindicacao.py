from django.db import models
from django.core.exceptions import ValidationError

from .instituicao import Instituicao
from .sala import Sala
from .perfil import Perfil
from .item import Item


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

    def clean(self):
        super().clean()
        if self.item_id:
            # 1. Bloqueia se o item já foi devolvido
            if self.item.status == Item.StatusItem.DEVOLVIDO:
                raise ValidationError(
                    {"item": "Este item já foi devolvido ao proprietário e não aceita novas reivindicações."}
                )

            # 2. Bloqueia se o item não estiver disponível (status != ENCONTRADO)
            if not self.pk and self.item.status != Item.StatusItem.ENCONTRADO:
                raise ValidationError(
                    {"item": "Este item não está disponível para reivindicação no momento."}
                )

            # 3. Garante que o autor e o item pertencem à mesma instituição
            if self.instituicao_id and self.item.instituicao_id != self.instituicao_id:
                raise ValidationError("A reivindicação deve pertencer à mesma instituição do item.")    

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)    
    
    class Meta:
        verbose_name = "Reivindicação"
        verbose_name_plural = "Reivindicações"
        ordering = ["-data"]  # Corrigido de data_criacao para data

