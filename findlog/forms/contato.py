from django import forms
from ..models import Contato

class ContatoForm(forms.ModelForm):
    class Meta:
        model = Contato
        fields = [
            "nome",
            "email",
            "telefone",
            "assunto",
            "mensagem",
        ]

        widgets = {
            "nome": forms.TextInput(attrs={
                "maxlength": 100,
            }),
            "email": forms.EmailInput(attrs={
                "maxlength": 100,
            }),
            "telefone": forms.TextInput(attrs={
                "maxlength": 15,
            }),
            "assunto": forms.Select(),
            "mensagem": forms.Textarea(attrs={
                "maxlength": 2000,
                "rows": 6,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Estes campos serão obrigatórios no formulário.
        for campo in [
            "nome",
            "email",
            "telefone",
            "assunto",
            "mensagem",
        ]:
            self.fields[campo].required = True
