from django import forms
from ..models import Categoria

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome", "descricao"]
        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Eletrônicos, Documentos, Acessórios",
                "id": "nome",
            }),
            "descricao": forms.Textarea(attrs={
                "class": "form-control form-control-custom",
                "rows": 3,
                "placeholder": "Ex: Celulares, carregadores, fones de ouvido e dispositivos eletrônicos em geral",
                "id": "descricao",
            }),
        }

    def clean_nome(self):
        nome = self.cleaned_data.get("nome", "").strip()
        if not nome:
            raise forms.ValidationError("O nome da categoria é obrigatório.")

        # Validação para evitar duplicidade de nomes iguais (case-insensitive)
        qs = Categoria.objects.filter(nome__iexact=nome)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Já existe uma categoria cadastrada com este nome.")

        return nome



