import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from ..models import Instituicao, VinculoInstituicao, Sala, Perfil
from ..utils import apenas_digitos, validar_cpf


class NovoUsuarioForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-custom",
            "placeholder": "Mínimo de 6 caracteres"
        }),
        min_length=6,
        label="Senha de Acesso"
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-custom",
            "placeholder": "Repita a senha"
        }),
        min_length=6,
        label="Confirmar Senha"
    )
    instituicao_cnpj = forms.ModelChoiceField(
        queryset=Instituicao.objects.filter(ativo=True),
        to_field_name="cnpj",
        empty_label="Selecione a instituição...",
        widget=forms.Select(attrs={"class": "form-select form-select-custom", "id": "instituicao_cnpj"}),
        label="Instituição Parceira"
    )
    sala_codigo = forms.ModelChoiceField(
        queryset=Sala.objects.all(),
        required=False,
        empty_label="Selecione a sala vinculada...",
        widget=forms.Select(attrs={"class": "form-select form-select-custom", "id": "sala_codigo"}),
        label="Sala Responsável"
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
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control form-control-custom", "placeholder": "Nome completo"}),
            "cpf": forms.TextInput(attrs={"class": "form-control form-control-custom cpf-format", "placeholder": "000.000.000-00"}),
            "data_nascimento": forms.DateInput(attrs={"class": "form-control form-control-custom", "type": "date"}),
            "telefone": forms.TextInput(attrs={"class": "form-control form-control-custom telefone-format", "placeholder": "(00) 00000-0000"}),
            "email": forms.EmailInput(attrs={"class": "form-control form-control-custom", "placeholder": "usuario@exemplo.com"}),
            "tipo": forms.Select(attrs={"class": "form-select form-select-custom"}),
            "foto": forms.FileInput(attrs={"class": "form-control form-control-custom", "accept": "image/*"}),
        }

    def clean_cpf(self):
        cpf_bruto = self.cleaned_data.get("cpf", "")
        cpf_limpo = re.sub(r"\D", "", str(cpf_bruto))

        if not cpf_limpo:
            raise forms.ValidationError("O CPF é obrigatório.")

        if len(cpf_limpo) != 11:
            raise forms.ValidationError("O CPF deve conter exatamente 11 dígitos numéricos.")

        if cpf_limpo == cpf_limpo[0] * 11:
            raise forms.ValidationError("Número de CPF inválido.")

        if Perfil.objects.filter(cpf=cpf_limpo).exists():
            raise forms.ValidationError("Já existe um usuário cadastrado com este CPF.")

        return cpf_limpo

    def clean_telefone(self):
        tel_bruto = self.cleaned_data.get("telefone", "")
        if not tel_bruto:
            return ""

        tel_limpo = re.sub(r"\D", "", str(tel_bruto))

        if len(tel_limpo) not in (10, 11):
            raise forms.ValidationError("O telefone deve conter DDD e número válidos (10 ou 11 dígitos).")

        return tel_limpo

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")
        tipo = cleaned_data.get("tipo")
        sala = cleaned_data.get("sala_codigo")

        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error("confirmar_senha", "As senhas informadas não coincidem.")

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
            instituicao = self.cleaned_data.get("instituicao_cnpj")
            if instituicao:
                VinculoInstituicao.objects.get_or_create(
                    perfil=usuario,
                    instituicao=instituicao,
                )

        return usuario


class AutoCadastroBaseForm(forms.ModelForm):
    senha = forms.CharField(
        label="Crie uma Senha",
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Mínimo de 6 caracteres",
                "autocomplete": "new-password",
            }
        ),
    )
    confirmar_senha = forms.CharField(
        label="Confirme sua Senha",
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Repita a senha digitada",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = Perfil
        fields = ["nome", "email", "cpf", "telefone", "codigo", "data_nascimento"]
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "form-control form-control-custom",
                    "placeholder": "Seu nome completo",
                    "required": True,
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control form-control-custom",
                    "placeholder": "seu.email@exemplo.com",
                    "required": True,
                }
            ),
            "cpf": forms.TextInput(
                attrs={
                    "class": "form-control form-control-custom cpf-format",
                    "placeholder": "000.000.000-00",
                    "required": True,
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "form-control form-control-custom telefone-format",
                    "placeholder": "(00) 00000-0000",
                }
            ),
            "codigo": forms.TextInput(
                attrs={
                    "class": "form-control form-control-custom",
                    "placeholder": "Matrícula ou SIAPE (opcional)",
                }
            ),
            "data_nascimento": forms.DateInput(
                attrs={
                    "class": "form-control form-control-custom",
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, instituicao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instituicao = instituicao

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if Perfil.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Este e-mail já está cadastrado no sistema. Faça login para vincular outra instituição."
            )
        return email

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf", "")
        cpf_limpo = apenas_digitos(cpf)
        validar_cpf(cpf_limpo)
        if Perfil.objects.filter(cpf=cpf_limpo).exists():
            raise forms.ValidationError(
                "Este CPF já possui cadastro no FindLog. Caso já tenha conta, faça login."
            )
        return cpf_limpo

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone", "")
        return apenas_digitos(telefone) if telefone else ""

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error("confirmar_senha", "As senhas informadas não coincidem.")

        return cleaned_data


class AutoCadastroUsuarioForm(AutoCadastroBaseForm):
    """Formulário público para autocadastro de Usuários Comuns (Alunos/Visitantes)."""

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.tipo = Perfil.TipoUsuario.USUARIO
        usuario.sala = None
        usuario.ativo = True
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.set_password(self.cleaned_data["senha"])

        if commit:
            usuario.save()
            if self.instituicao:
                VinculoInstituicao.objects.get_or_create(
                    perfil=usuario,
                    instituicao=self.instituicao,
                )
        return usuario


class AutoCadastroServidorForm(AutoCadastroBaseForm):
    """Formulário público para autocadastro de Servidores (aguarda aprovação institucional)."""

    sala = forms.ModelChoiceField(
        queryset=Sala.objects.none(),
        required=True,
        empty_label="Selecione seu setor / sala de atuação...",
        label="Sala / Setor de Atuação",
        widget=forms.Select(
            attrs={
                "class": "form-select form-select-custom",
                "required": True,
            }
        ),
    )

    class Meta(AutoCadastroBaseForm.Meta):
        fields = AutoCadastroBaseForm.Meta.fields + ["sala"]

    def __init__(self, *args, instituicao=None, **kwargs):
        super().__init__(*args, instituicao=instituicao, **kwargs)
        if self.instituicao:
            self.fields["sala"].queryset = Sala.objects.filter(
                instituicao=self.instituicao,
                ativa=True,
            ).order_by("predio", "andar", "nome")

    def clean_sala(self):
        sala = self.cleaned_data.get("sala")
        if sala and self.instituicao and sala.instituicao != self.instituicao:
            raise forms.ValidationError("A sala selecionada não pertence a esta instituição.")
        return sala

    def save(self, commit=True):
        servidor = super().save(commit=False)
        servidor.tipo = Perfil.TipoUsuario.SERVIDOR
        servidor.ativo = False
        servidor.is_staff = False
        servidor.is_superuser = False
        servidor.set_password(self.cleaned_data["senha"])

        if commit:
            servidor.save()
            if self.instituicao:
                VinculoInstituicao.objects.get_or_create(
                    perfil=servidor,
                    instituicao=self.instituicao,
                )
        return servidor


class ServidorCadastroColegaForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-custom", "placeholder": "Senha inicial"}
        ),
        min_length=6,
        label="Senha Provisória",
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-custom", "placeholder": "Repita a senha"}
        ),
        min_length=6,
        label="Confirmar Senha",
    )

    class Meta:
        model = Perfil
        fields = [
            "nome",
            "username",
            "cpf",
            "email",
            "telefone",
            "tipo",
            "sala",
        ]
        widgets = {
            "nome": forms.TextInput(
                attrs={"class": "form-control form-control-custom", "placeholder": "Nome completo"}
            ),
            "username": forms.TextInput(
                attrs={"class": "form-control form-control-custom", "placeholder": "nome.sobrenome"}
            ),
            "cpf": forms.TextInput(
                attrs={
                    "class": "form-control form-control-custom cpf-format",
                    "placeholder": "000.000.000-00",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control form-control-custom",
                    "placeholder": "usuario@instituicao.edu.br",
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "form-control form-control-custom telefone-format",
                    "placeholder": "(00) 00000-0000",
                }
            ),
            "tipo": forms.Select(
                attrs={"class": "form-select form-select-custom", "id": "id_tipo"}
            ),
            "sala": forms.TextInput(
                attrs={
                    "class": "form-control form-control-custom",
                    "id": "id_sala",
                    "list": "lista-salas-colega",
                    "placeholder": "Digite para buscar a sala de responsabilidade...",
                    "autocomplete": "off",
                }
            ),
        }

    def __init__(self, *args, instituicao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instituicao = instituicao

        # 1. Limita as opções de tipo: APENAS Servidor (3) ou Usuário (2)
        tipos_permitidos = [
            (Perfil.TipoUsuario.USUARIO, "Usuário Comum / Aluno"),
            (Perfil.TipoUsuario.SERVIDOR, "Servidor"),
        ]
        self.fields["tipo"].choices = tipos_permitidos

        # 2. Filtra estritamente as salas ativas da instituição ativa
        if self.instituicao:
            self.salas_disponiveis = Sala.objects.filter(
                instituicao=self.instituicao,
                ativa=True,
            ).order_by("predio", "nome")
        else:
            self.salas_disponiveis = Sala.objects.none()

        # Converte o campo 'sala' para CharField para aceitar texto do <datalist>
        campo_sala_antigo = self.fields["sala"]
        self.fields["sala"] = forms.CharField(
            required=False,
            label=campo_sala_antigo.label,
            widget=campo_sala_antigo.widget,
        )
        self.fields["sala"].queryset = self.salas_disponiveis

        # Mapeia "Nome - Prédio" (ou nome da sala) -> objeto Sala
        self._mapa_salas = {}
        for sala in self.salas_disponiveis:
            rotulo = self._formatar_rotulo_sala(sala)
            self._mapa_salas[rotulo.lower()] = sala
            self._mapa_salas.setdefault(sala.nome.strip().lower(), sala)

        if not self.is_bound and self.instance and self.instance.pk and self.instance.sala:
            self.initial["sala"] = self._formatar_rotulo_sala(self.instance.sala)

    @staticmethod
    def _formatar_rotulo_sala(sala):
        return f"{sala.nome} - {sala.predio}" if sala.predio else sala.nome

    @property
    def opcoes_datalist_salas(self):
        """Retorna os rótulos formatados para renderizar no <datalist> da template."""
        return [self._formatar_rotulo_sala(sala) for sala in self.salas_disponiveis]

    def clean_sala(self):
        valor = str(self.data.get(self.add_prefix("sala")) or "").strip()
        if not valor:
            return None

        sala = self._mapa_salas.get(valor.lower())
        if not sala:
            raise forms.ValidationError(
                "Selecione uma sala válida da lista de sugestões da instituição."
            )
        return sala

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf", "")
        cpf_limpo = re.sub(r"\D", "", str(cpf))
        if len(cpf_limpo) != 11:
            raise forms.ValidationError("O CPF precisa conter 11 dígitos.")
        if Perfil.objects.filter(cpf=cpf_limpo).exists():
            raise forms.ValidationError("Já existe um perfil cadastrado com este CPF.")
        return cpf_limpo

    def clean_telefone(self):
        tel = self.cleaned_data.get("telefone", "")
        return re.sub(r"\D", "", str(tel)) if tel else ""

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")
        tipo = cleaned_data.get("tipo")
        sala = cleaned_data.get("sala")

        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error("confirmar_senha", "As senhas não coincidem.")

        if tipo == Perfil.TipoUsuario.SERVIDOR and not sala:
            self.add_error("sala", "É obrigatório associar uma sala para perfis do tipo Servidor.")

        if tipo == Perfil.TipoUsuario.USUARIO:
            cleaned_data["sala"] = None

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["senha"])
        usuario.ativo = True
        usuario.is_staff = False
        usuario.is_superuser = False

        if commit:
            usuario.save()
            if self.instituicao:
                VinculoInstituicao.objects.get_or_create(
                    perfil=usuario,
                    instituicao=self.instituicao,
                )
        return usuario


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


class ServidorAlterarSenhaForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Senha atual"
        self.fields["new_password1"].label = "Nova senha"
        self.fields["new_password2"].label = "Confirmar nova senha"

        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


class ServidorEditarUserForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ["nome", "email", "data_nascimento", "telefone", "foto", "sala"]
        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Seu nome completo",
                "required": True,
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control form-control-custom bg-light",
                "readonly": True,
            }),
            "data_nascimento": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "class": "form-control form-control-custom",
                    "type": "date",
                },
            ),
            "telefone": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "(00) 00000-0000",
                "maxlength": "15",
                "id": "telefone",
            }),
            "foto": forms.FileInput(attrs={
                "class": "form-control form-control-custom",
                "accept": "image/png, image/jpeg, image/webp",
            }),
            "sala": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "list": "lista-salas-servidor",
                "placeholder": "Digite para buscar sua sala/setor (Opcional)...",
                "autocomplete": "off",
            }),
        }

    def __init__(self, *args, instituicao=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].disabled = True
        self.fields["email"].required = False

        if instituicao is None and self.instance and self.instance.pk:
            instituicao = self.instance.instituicao.filter(ativo=True).first()

        if instituicao:
            self.salas_disponiveis = Sala.objects.filter(
                instituicao=instituicao,
                ativa=True,
            ).order_by("predio", "nome")
        else:
            self.salas_disponiveis = Sala.objects.none()

        # Converte o campo 'sala' para CharField para aceitar texto do <datalist>
        campo_sala_antigo = self.fields["sala"]
        self.fields["sala"] = forms.CharField(
            required=False,
            label=campo_sala_antigo.label,
            widget=campo_sala_antigo.widget,
        )
        self.fields["sala"].queryset = self.salas_disponiveis

        self._mapa_salas = {}
        for sala in self.salas_disponiveis:
            rotulo = self._formatar_rotulo_sala(sala)
            self._mapa_salas[rotulo.lower()] = sala
            self._mapa_salas.setdefault(sala.nome.strip().lower(), sala)

        if not self.is_bound and self.instance and self.instance.pk and self.instance.sala:
            self.initial["sala"] = self._formatar_rotulo_sala(self.instance.sala)

    @staticmethod
    def _formatar_rotulo_sala(sala):
        return f"{sala.nome} - {sala.predio}" if sala.predio else sala.nome

    @property
    def opcoes_datalist_salas(self):
        """Retorna os rótulos formatados para renderizar no <datalist> da template."""
        return [self._formatar_rotulo_sala(sala) for sala in self.salas_disponiveis]

    def clean_sala(self):
        valor = str(self.data.get(self.add_prefix("sala")) or "").strip()
        if not valor:
            return None

        sala = self._mapa_salas.get(valor.lower())
        if not sala:
            raise forms.ValidationError(
                "Selecione uma sala válida da lista de sugestões da instituição."
            )
        return sala

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone")
        if not telefone:
            return ""

        somente_numeros = apenas_digitos(telefone)

        if len(somente_numeros) not in (10, 11):
            raise forms.ValidationError(
                "Informe um telefone válido com DDD (10 ou 11 dígitos)."
            )

        return somente_numeros


class ServidorEditarPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = [
            "telefone",
            "foto",
        ]
        widgets = {
            "telefone": forms.TextInput(attrs={"class": "form-control", "placeholder": "(86) 99999-9999", "id": "telefone"}),
            "foto": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }