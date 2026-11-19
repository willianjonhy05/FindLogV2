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
            "local_devolucao": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "id": "id_local_devolucao",
                "list": "lista-salas-devolucao",
                "placeholder": "Digite para buscar a sala de retirada...",
                "autocomplete": "off",
            }),
            "resposta_admin": forms.Textarea(attrs={
                "class": "form-control form-control-custom",
                "rows": 4,
                "placeholder": "Informe o parecer da análise, instruções de retirada ou motivo da recusa...",
            }),
        }

    def __init__(self, *args, instituicao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instituicao = instituicao

        if instituicao:
            self.salas_disponiveis = Sala.objects.filter(
                instituicao=instituicao,
                ativa=True,
            ).order_by("predio", "nome")
        else:
            self.salas_disponiveis = Sala.objects.none()

        self.fields["local_devolucao"].queryset = self.salas_disponiveis
        self.fields["local_devolucao"].required = False

        # Mapeia "Nome - Prédio" (ou nome da sala) -> objeto Sala
        self._mapa_salas = {}
        for sala in self.salas_disponiveis:
            rotulo = self._formatar_rotulo_sala(sala)
            self._mapa_salas[rotulo.lower()] = sala
            # Também aceita caso o servidor digite apenas o nome exato da sala (se único)
            self._mapa_salas.setdefault(sala.nome.strip().lower(), sala)

        # Exibe o texto legível no input ao abrir uma reivindicação que já possui local_devolucao
        if not self.is_bound and self.instance and self.instance.pk and self.instance.local_devolucao:
            self.initial["local_devolucao"] = self._formatar_rotulo_sala(self.instance.local_devolucao)

    @staticmethod
    def _formatar_rotulo_sala(sala):
        return f"{sala.nome} - {sala.predio}" if sala.predio else sala.nome

    @property
    def opcoes_datalist_salas(self):
        """Retorna a lista de rótulos formatados para renderizar no <datalist> da template."""
        return [self._formatar_rotulo_sala(sala) for sala in self.salas_disponiveis]

    def clean_local_devolucao(self):
        valor = self.data.get(self.add_prefix("local_devolucao"), "").strip()
        if not valor:
            return None

        sala = self._mapa_salas.get(valor.lower())
        if not sala:
            raise forms.ValidationError(
                "Selecione uma sala válida da lista de sugestões da instituição."
            )
        return sala

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


