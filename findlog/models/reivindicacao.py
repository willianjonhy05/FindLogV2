from django.db import models
from django.core.exceptions import ValidationError

from .instituicao import Instituicao
from .sala import Sala
from .perfil import Perfil
from .item import Item

MENSAGEM_REJEICAO_AUTOMATICA = (
    "Reivindicação encerrada automaticamente: outro usuário já comprovou "
    "a propriedade deste item e a devolução foi concluída."
)


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
            # 1. Bloqueia novas reivindicações se o item já foi devolvido
            if self.item.status == Item.StatusItem.DEVOLVIDO and not self.pk:
                raise ValidationError(
                    {"item": "Este item já foi devolvido ao proprietário e não aceita novas reivindicações."}
                )

            # 2. Bloqueia criação se o item não estiver disponível
            if not self.pk and self.item.status != Item.StatusItem.ENCONTRADO:
                raise ValidationError(
                    {"item": "Este item não está disponível para reivindicação no momento."}
                )

            # 3. Impede concluir uma reivindicação se outra já foi concluída para o mesmo item
            if self.status == self.StatusReivindicacao.CONCLUIDA:
                existe_outra_concluida = Reivindicacao.objects.filter(
                    item=self.item,
                    status=self.StatusReivindicacao.CONCLUIDA
                ).exclude(pk=self.pk).exists()

                if existe_outra_concluida:
                    raise ValidationError(
                        "Este item já teve a devolução concluída em outra reivindicação."
                    )

            # 4. Garante que a reivindicação e o item pertencem à mesma instituição
            if self.instituicao_id and self.item.instituicao_id != self.instituicao_id:
                raise ValidationError("A reivindicação deve pertencer à mesma instituição do item.")

    def save(self, *args, **kwargs):
        status_anterior = None

        if self.pk:
            status_anterior = (
                Reivindicacao.objects.filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )

        self.full_clean()

        with transaction.atomic():
            # Preenche ou limpa data_devolucao conforme mudança de status
            if self.status == self.StatusReivindicacao.CONCLUIDA and not self.data_devolucao:
                self.data_devolucao = timezone.now()
            elif status_anterior == self.StatusReivindicacao.CONCLUIDA and self.status != self.StatusReivindicacao.CONCLUIDA:
                self.data_devolucao = None

            super().save(*args, **kwargs)

            # Cenário 1: Reivindicação marcada como CONCLUÍDA
            if self.status == self.StatusReivindicacao.CONCLUIDA:
                # Atualiza o item para DEVOLVIDO
                if self.item.status != Item.StatusItem.DEVOLVIDO:
                    self.item.status = Item.StatusItem.DEVOLVIDO
                    self.item.save(update_fields=["status"])

                # Rejeita todas as outras reivindicações ainda abertas para o mesmo item
                outras_abertas = Reivindicacao.objects.filter(
                    item=self.item,
                    status__in=[
                        self.StatusReivindicacao.PENDENTE,
                        self.StatusReivindicacao.EM_ANALISE,
                        self.StatusReivindicacao.APROVADA,
                    ],
                ).exclude(pk=self.pk)

                campos_atualizacao = {
                    "status": self.StatusReivindicacao.REJEITADA,
                    "resposta_admin": MENSAGEM_REJEICAO_AUTOMATICA,
                }
                if self.responsavel_admin_id:
                    campos_atualizacao["responsavel_admin"] = self.responsavel_admin

                outras_abertas.update(**campos_atualizacao)

            # Cenário 2: Estava CONCLUÍDA e voltou para outro status por engano
            elif status_anterior == self.StatusReivindicacao.CONCLUIDA:
                existe_outra_concluida = Reivindicacao.objects.filter(
                    item=self.item,
                    status=self.StatusReivindicacao.CONCLUIDA
                ).exclude(pk=self.pk).exists()

                if not existe_outra_concluida and self.item.status == Item.StatusItem.DEVOLVIDO:
                    self.item.status = Item.StatusItem.ENCONTRADO
                    self.item.save(update_fields=["status"])

                    # Reabre apenas as reivindicações que foram rejeitadas pela mensagem automática
                    # (preservando as que tinham sido rejeitadas manualmente por outros motivos)
                    Reivindicacao.objects.filter(
                        item=self.item,
                        status=self.StatusReivindicacao.REJEITADA,
                        resposta_admin=MENSAGEM_REJEICAO_AUTOMATICA,
                    ).exclude(pk=self.pk).update(
                        status=self.StatusReivindicacao.EM_ANALISE,
                        resposta_admin="",
                    )

    class Meta:
        verbose_name = "Reivindicação"
        verbose_name_plural = "Reivindicações"
        ordering = ["-data"]