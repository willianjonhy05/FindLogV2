from django import forms
from ..models import Reivindicacao, Sala

class ReivindicacaoUpdateForm(forms.ModelForm):
    class Meta:
        model = Reivindicacao
        fields = [
            "status",
            "resposta_admin",
            "responsavel_admin",
            "local_devolucao",
            "data_devolucao",
        ]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select form-select-custom"}),
            "resposta_admin": forms.Textarea(attrs={
                "class": "form-control form-control-custom",
                "rows": 4,
                "placeholder": "Parecer ou orientações da administração para o solicitante..."
            }),
            "responsavel_admin": forms.Select(attrs={"class": "form-select form-select-custom"}),
            "local_devolucao": forms.Select(attrs={"class": "form-select form-select-custom"}),
            "data_devolucao": forms.DateTimeInput(attrs={"class": "form-control form-control-custom", "type": "datetime-local"}),
        }        


class ServidorAnaliseReivindicacaoForm(forms.ModelForm):
    class Meta:
        model = Reivindicacao
        fields = [
            "status",
            "local_devolucao",
            "resposta_admin",
        ]
        widgets = {
            "status": forms.Select(attrs={
                "class": "form-select form-select-custom",
                "id": "id_status_reivindicacao",
            }),
            "local_devolucao": forms.Select(attrs={
                "class": "form-select form-select-custom",
                "id": "id_local_devolucao",
            }),
            "resposta_admin": forms.Textarea(attrs={
                "class": "form-control form-control-custom",
                "rows": 4,
                "placeholder": "Informe o parecer da análise, instruções de retirada ou motivo da recusa...",
            }),
        }

    def __init__(self, *args, instituicao=None, **kwargs):
        super().__init__(*args, **kwargs)

        if instituicao:
            self.fields["local_devolucao"].queryset = Sala.objects.filter(
                instituicao=instituicao,
                ativa=True,
            ).order_by("predio", "nome")
        else:
            self.fields["local_devolucao"].queryset = Sala.objects.none()

        self.fields["local_devolucao"].empty_label = "Selecione a sala para retirada/devolução..."

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        local_devolucao = cleaned_data.get("local_devolucao")
        resposta_admin = cleaned_data.get("resposta_admin", "").strip()

        # Exige local de retirada caso seja Aprovada
        if status == Reivindicacao.StatusReivindicacao.APROVADA and not local_devolucao:
            self.add_error(
                "local_devolucao",
                "Informe a sala onde o usuário deverá comparecer para retirar o item.",
            )

        # Exige justificativa caso seja Rejeitada
        if status == Reivindicacao.StatusReivindicacao.REJEITADA and not resposta_admin:
            self.add_error(
                "resposta_admin",
                "É obrigatório informar o motivo da rejeição para o solicitante.",
            )

        return cleaned_data    


