from django.db import models
from ..utils import gerar_codigo_aleatorio
from .instituicao import Instituicao
from .sala import Sala
from .categoria import Categoria
from .perfil import Perfil

import base64
from io import BytesIO
import qrcode

import uuid

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


    @property
    def qr_code(self):
        dados = self.uuid
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(dados)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        string_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{string_b64}"


    def __str__(self):
        return f"{self.nome} ({self.codigo})" if self.nome else f"Item {self.codigo}"

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"