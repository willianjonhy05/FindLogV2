from django import forms
from ..models import Item, Categoria, Sala

class ItemUpdateForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "nome",
            "categoria",
            "instituicao",
            "status",
            "dono",
            "tamanho",
            "cor",
            "material",
            "marca_ou_modelo",
            "local",
            "local_guardado",
            "data_devolucao",
            "foto",
            "descricao",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control form-control-custom", "placeholder": "Ex: Chaveiro com 3 chaves"}),
            "categoria": forms.Select(attrs={"class": "form-select form-select-custom"}),
            "instituicao": forms.Select(attrs={"class": "form-select form-select-custom"}),
            "status": forms.Select(attrs={"class": "form-select form-select-custom"}),
            "dono": forms.Select(attrs={"class": "form-select form-select-custom"}),
            "tamanho": forms.TextInput(attrs={"class": "form-control form-control-custom", "placeholder": "Ex: Pequeno, Médio, 15cm"}),
            "cor": forms.TextInput(attrs={"class": "form-control form-control-custom", "placeholder": "Ex: Preto, Azul metálico"}),
            "material": forms.TextInput(attrs={"class": "form-control form-control-custom", "placeholder": "Ex: Plástico, Couro, Metal"}),
            "marca_ou_modelo": forms.TextInput(attrs={"class": "form-control form-control-custom", "placeholder": "Ex: Samsung Galaxy S21"}),
            "local": forms.Select(attrs={"class": "form-select form-select-custom"}),
            "local_guardado": forms.Select(attrs={"class": "form-select form-select-custom"}),
            "data_devolucao": forms.DateTimeInput(attrs={"class": "form-control form-control-custom", "type": "datetime-local"}),
            "foto": forms.FileInput(attrs={"class": "form-control form-control-custom"}),
            "descricao": forms.Textarea(attrs={"class": "form-control form-control-custom", "rows": 4, "placeholder": "Descreva detalhes específicos do item..."}),
        }


class ServidorItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "nome",
            "categoria",
            "status",
            "local",
            "local_guardado",
            "marca_ou_modelo",
            "cor",
            "tamanho",
            "material",
            "foto",
            "descricao",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Garrafa térmica, Mochila preta...",
                "required": True,
            }),
            "categoria": forms.Select(attrs={
                "class": "form-select form-select-custom select-pesquisavel",
                "required": True,
            }),
            "status": forms.Select(attrs={
                "class": "form-select form-select-custom",
                "required": True,
            }),
            "local": forms.Select(attrs={
                "class": "form-select form-select-custom select-pesquisavel",
            }),
            "local_guardado": forms.Select(attrs={
                "class": "form-select form-select-custom select-pesquisavel",
            }),
            "marca_ou_modelo": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Invicta, Dell, Samsung...",
            }),
            "cor": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Azul, Preto, Cinza...",
            }),
            "tamanho": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Médio, 500ml, 15 polegadas...",
            }),
            "material": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Inox, Plástico, Tecido...",
            }),
            "foto": forms.FileInput(attrs={
                "class": "form-control form-control-custom",
                "accept": "image/*",
                "capture": "environment",
            }),
            "descricao": forms.Textarea(attrs={
                "class": "form-control form-control-custom",
                "rows": 3,
                "placeholder": "Descreva características gerais sem revelar segredos que apenas o dono saberia...",
            }),
        }

    def __init__(self, *args, instituicao=None, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Filtra apenas categorias ativas
        self.fields["categoria"].queryset = Categoria.objects.filter(ativa=True).order_by("nome")
        self.fields["categoria"].empty_label = "Digite para buscar a categoria..."

        # 2. Filtra as salas estritamente para a instituição ativa do servidor
        if instituicao:
            salas_qs = Sala.objects.filter(instituicao=instituicao, ativa=True).order_by("predio", "nome")
            self.fields["local"].queryset = salas_qs
            self.fields["local_guardado"].queryset = salas_qs
        else:
            self.fields["local"].queryset = Sala.objects.none()
            self.fields["local_guardado"].queryset = Sala.objects.none()

        self.fields["local"].empty_label = "Digite para buscar onde foi encontrado... (Opcional)"
        self.fields["local_guardado"].empty_label = "Digite para buscar onde está guardado... (Opcional)"