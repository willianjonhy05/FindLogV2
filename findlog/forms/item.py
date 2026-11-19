from django import forms
from ..models import Item, Categoria, Sala, Perfil

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

class ItemDatalistMixin:
    """
    Configura campos de datalist para 'categoria', 'local' e 'local_guardado',
    garantindo isolamento multi-tenant para os locais/salas da instituição do servidor.
    """

    def _configurar_datalists_item(self, instituicao=None, user=None):
        # 1. Categorias ativas
        self.categorias_disponiveis = Categoria.objects.filter(ativa=True).order_by("nome")
        self._mapa_categorias = {
            cat.nome.strip().lower(): cat for cat in self.categorias_disponiveis
        }

        if "categoria" in self.fields:
            self.fields["categoria"].queryset = self.categorias_disponiveis
            if not self.is_bound and self.instance and self.instance.pk and self.instance.categoria:
                self.initial["categoria"] = self.instance.categoria.nome

        # 2. Salas/locais ativos restritos à instituição (ou instituições vinculadas ao usuário)
        if instituicao is None and self.instance and self.instance.pk and self.instance.instituicao_id:
            instituicao = self.instance.instituicao

        if instituicao is not None:
            self.salas_disponiveis = Sala.objects.filter(
                instituicao=instituicao,
                ativa=True,
            ).order_by("predio", "nome")
        elif user is not None and getattr(user, "is_authenticated", False):
            self.salas_disponiveis = Sala.objects.filter(
                instituicao__in=user.instituicao.filter(ativo=True),
                ativa=True,
            ).order_by("instituicao__nome", "predio", "nome")
        else:
            self.salas_disponiveis = Sala.objects.none()

        self._mapa_salas = {}
        for sala in self.salas_disponiveis:
            rotulo = self._formatar_rotulo_sala(sala)
            self._mapa_salas[rotulo.lower()] = sala
            self._mapa_salas.setdefault(sala.nome.strip().lower(), sala)

        for campo_sala in ("local", "local_guardado"):
            if campo_sala in self.fields:
                self.fields[campo_sala].queryset = self.salas_disponiveis
                self.fields[campo_sala].required = False

                if not self.is_bound and self.instance and self.instance.pk:
                    sala_atual = getattr(self.instance, campo_sala, None)
                    if sala_atual:
                        self.initial[campo_sala] = self._formatar_rotulo_sala(sala_atual)

    @staticmethod
    def _formatar_rotulo_sala(sala):
        return f"{sala.nome} - {sala.predio}" if sala.predio else sala.nome

    @property
    def opcoes_datalist_categorias(self):
        return [cat.nome for cat in self.categorias_disponiveis]

    @property
    def opcoes_datalist_salas(self):
        return [self._formatar_rotulo_sala(sala) for sala in self.salas_disponiveis]

    def clean_categoria(self):
        valor = self.data.get(self.add_prefix("categoria"), "").strip()
        if not valor:
            if self.fields["categoria"].required:
                raise forms.ValidationError("Selecione uma categoria válida da lista.")
            return None

        categoria = self._mapa_categorias.get(valor.lower())
        if not categoria:
            raise forms.ValidationError("Selecione uma categoria válida da lista de sugestões.")
        return categoria

    def _resolver_sala(self, nome_campo):
        valor = self.data.get(self.add_prefix(nome_campo), "").strip()
        if not valor:
            return None

        sala = self._mapa_salas.get(valor.lower())
        if not sala:
            raise forms.ValidationError(
                "Selecione uma sala válida da lista de sugestões da instituição."
            )
        return sala

    def clean_local(self):
        return self._resolver_sala("local")

    def clean_local_guardado(self):
        return self._resolver_sala("local_guardado")


class ServidorItemForm(ItemDatalistMixin, forms.ModelForm):
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
            "categoria": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "list": "lista-categorias-item",
                "placeholder": "Digite para buscar a categoria...",
                "autocomplete": "off",
                "required": True,
            }),
            "status": forms.Select(attrs={
                "class": "form-select form-select-custom",
                "required": True,
            }),
            "local": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "list": "lista-salas-item",
                "placeholder": "Digite para buscar onde foi encontrado... (Opcional)",
                "autocomplete": "off",
            }),
            "local_guardado": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "list": "lista-salas-item",
                "placeholder": "Digite para buscar onde está guardado... (Opcional)",
                "autocomplete": "off",
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

    def __init__(self, *args, instituicao=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].required = True
        self._configurar_datalists_item(instituicao=instituicao, user=user)


class ServidorAtualizarItemForm(ItemDatalistMixin, forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "categoria",
            "nome",
            "dono",
            "cor",
            "tamanho",
            "material",
            "marca_ou_modelo",
            "local",
            "local_guardado",
            "foto",
            "descricao",
        ]
        widgets = {
            "categoria": forms.TextInput(attrs={
                "class": "form-control",
                "list": "lista-categorias-item",
                "placeholder": "Digite para buscar a categoria...",
                "autocomplete": "off",
                "required": True,
            }),
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "dono": forms.Select(attrs={"class": "form-select"}),
            "cor": forms.TextInput(attrs={"class": "form-control"}),
            "tamanho": forms.TextInput(attrs={"class": "form-control"}),
            "material": forms.TextInput(attrs={"class": "form-control"}),
            "marca_ou_modelo": forms.TextInput(attrs={"class": "form-control"}),
            "local": forms.TextInput(attrs={
                "class": "form-control",
                "list": "lista-salas-item",
                "placeholder": "Digite para buscar onde foi encontrado... (Opcional)",
                "autocomplete": "off",
            }),
            "local_guardado": forms.TextInput(attrs={
                "class": "form-control",
                "list": "lista-salas-item",
                "placeholder": "Digite para buscar onde está guardado... (Opcional)",
                "autocomplete": "off",
            }),
            "foto": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
                "capture": "environment",
            }),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        instituicao = kwargs.pop("instituicao", None)
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["categoria"].required = True
        self._configurar_datalists_item(instituicao=instituicao, user=user)

        # Restringe também o select de dono aos membros da mesma instituição
        if instituicao and "dono" in self.fields:
            self.fields["dono"].queryset = Perfil.objects.filter(
                instituicao=instituicao,
                ativo=True,
            ).order_by("nome")