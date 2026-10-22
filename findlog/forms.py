
from django import forms
from findlog.models import Contato, Instituicao, Categoria, Perfil, Sala, Item, Reivindicacao
from .utils import apenas_digitos
from django.contrib.auth import authenticate


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


class InstituicaoForm(forms.ModelForm):
    class Meta:
        model = Instituicao
        fields = ["cnpj", "nome", "endereco", "telefone", "email", "ativo"]

    def clean_cnpj(self):
        # Se estiver editando uma instância existente, mantém o PK original
        if self.instance.pk:
            return self.instance.pk

        cnpj = self.cleaned_data.get("cnpj", "")
        cnpj_limpo = apenas_digitos(cnpj)
        if Instituicao.objects.filter(pk=cnpj_limpo).exists():
            raise forms.ValidationError("Já existe uma instituição com este CNPJ.")
        return cnpj_limpo

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone", "")
        return apenas_digitos(telefone) if telefone else ""


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



class LoginForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={
            "class": "form-control form-control-custom",
            "placeholder": "nome@exemplo.com",
            "autocomplete": "email",
            "required": True,
        })
    )
    senha = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-custom",
            "placeholder": "Sua senha de acesso",
            "autocomplete": "current-password",
            "required": True,
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        senha = cleaned_data.get("senha")

        if email and senha:
            # Como USERNAME_FIELD = 'email', authenticate aceita username=email
            self.user = authenticate(username=email, password=senha)
            if not self.user:
                raise forms.ValidationError("E-mail ou senha incorretos.")
            if not self.user.is_active or not self.user.ativo:
                raise forms.ValidationError("Esta conta de acesso está desativada.")

        return cleaned_data


class NovoUsuarioForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-custom"}),
        min_length=6
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-custom"}),
        min_length=6
    )
    instituicao_cnpj = forms.ModelChoiceField(
        queryset=Instituicao.objects.filter(ativo=True),
        to_field_name="cnpj",
        empty_label="Selecione a instituição...",
        widget=forms.Select(attrs={"class": "form-select form-select-custom", "id": "instituicao_cnpj"})
    )
    sala_codigo = forms.ModelChoiceField(
        queryset=Sala.objects.all(),
        required=False,
        empty_label="Selecione a sala vinculada...",
        widget=forms.Select(attrs={"class": "form-select form-select-custom", "id": "sala_codigo"})
    )

    class Meta:
        model = Perfil
        fields = [
            "nome",
            "cpf",
            "data_nascimento",
            "telefone",
            "email",
            "tipo",
            "foto",
        ]

    def clean_cpf(self):
        cpf = apenas_digitos(self.cleaned_data.get("cpf", ""))
        if Perfil.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError("Já existe um usuário cadastrado com este CPF.")
        return cpf

    def clean_telefone(self):
        tel = self.cleaned_data.get("telefone", "")
        return apenas_digitos(tel) if tel else ""

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")
        tipo = cleaned_data.get("tipo")
        sala = cleaned_data.get("sala_codigo")

        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error("confirmar_senha", "As senhas informadas não coincidem.")

        # Validação obrigatória da sala para Servidores
        if tipo == Perfil.TipoUsuario.SERVIDOR and not sala:
            self.add_error("sala_codigo", "É obrigatório associar uma sala para usuários do tipo Servidor.")

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["senha"])
        
        if self.cleaned_data.get("tipo") == Perfil.TipoUsuario.SERVIDOR:
            usuario.sala = self.cleaned_data.get("sala_codigo")
        else:
            usuario.sala = None

        if commit:
            usuario.save()
            # Vincula a instituição através do modelo intermediário VinculoInstituicao
            instituicao = self.cleaned_data.get("instituicao_cnpj")
            if instituicao:
                from findlog.models import VinculoInstituicao
                VinculoInstituicao.objects.get_or_create(
                    perfil=usuario,
                    instituicao=instituicao,
                    defaults={"ativo": True}
                )

        return usuario    
    


class SalaForm(forms.ModelForm):
    instituicao = forms.ModelChoiceField(
        queryset=Instituicao.objects.filter(ativo=True),
        empty_label="Selecione a instituição...",
        widget=forms.Select(attrs={"class": "form-select form-select-custom", "id": "instituicao"})
    )

    class Meta:
        model = Sala
        fields = [
            "nome",
            "predio",
            "andar",
            "laboratorio",
            "sala_de_aula",
            "instituicao",
            "ativa",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: 101, B-04, Lab-02",
                "id": "nome",
            }),
            "predio": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Bloco A, Prédio Central",
                "id": "predio",
            }),
            "andar": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Térreo, 1º Andar",
                "id": "andar",
            }),
            "laboratorio": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "laboratorio"}),
            "sala_de_aula": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "sala_de_aula"}),
            "ativa": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "ativa"}),
        }    



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



class EditarMeuPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["nome", "email", "data_nascimento", "telefone", "foto"]
        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Seu nome completo"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "seu.email@exemplo.com"
            }),
            "data_nascimento": forms.DateInput(attrs={
                "class": "form-control form-control-custom",
                "type": "date"
            }),
            "telefone": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "(00) 00000-0000"
            }),
            "foto": forms.FileInput(attrs={
                "class": "form-control form-control-custom",
                "accept": "image/png, image/jpeg, image/webp"
            }),
        }


class TrocarMinhaSenhaForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control form-control-custom"})
            field.widget.attrs.pop("autofocus", None)        