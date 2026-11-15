from django.db import models
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from ..utils import validar_cnpj, apenas_digitos, formatar_cnpj, formatar_telefone


class Instituicao(models.Model):
    cnpj = models.CharField(
        "CNPJ da Instituição", max_length=14, primary_key=True, validators=[validar_cnpj]
    )
    nome = models.CharField("Nome da Instituição", max_length=255)
    endereco = models.CharField(
        "Endereço da Instituição",
        max_length=100,
        help_text="Digite o endereço de onde a plataforma será utilizada",
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

    @property
    def token_convite(self):
        """Gera um token assinado e seguro a partir do CNPJ (sem alterar o banco)."""
        signer = signing.TimestampSigner(salt="findlog-convite-instituicao")
        return signer.sign(self.cnpj)

    @classmethod
    def obter_por_token(cls, token, max_age=None):
        """
        Valida o token assinado e retorna a Instituicao ativa correspondente.
        max_age (opcional): tempo em segundos para expiração (ex: 86400 * 7 = 7 dias).
        """
        signer = signing.TimestampSigner(salt="findlog-convite-instituicao")
        try:
            cnpj = signer.unsign(token, max_age=max_age)
            return cls.objects.filter(cnpj=cnpj, ativo=True).first()
        except (BadSignature, SignatureExpired):
            return None

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Instituição"
        verbose_name_plural = "Instituições"
