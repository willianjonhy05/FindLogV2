from django import forms
from ..models import Instituicao, VinculoInstituicao, Sala, Perfil
from ..utils import apenas_digitos, validar_cpf
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model

import re

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
        # Remove espaços, pontos, traços, símbolos e letras
        cpf_limpo = re.sub(r"\D", "", str(cpf_bruto))

        if not cpf_limpo:
            raise forms.ValidationError("O CPF é obrigatório.")

        if len(cpf_limpo) != 11:
            raise forms.ValidationError("O CPF deve conter exatamente 11 dígitos numéricos.")

        # Impede sequências repetidas óbvias (ex: 111.111.111-11)
        if cpf_limpo == cpf_limpo[0] * 11:
            raise forms.ValidationError("Número de CPF inválido.")

        if Perfil.objects.filter(cpf=cpf_limpo).exists():
            raise forms.ValidationError("Já existe um usuário cadastrado com este CPF.")

        return cpf_limpo

    def clean_telefone(self):
        tel_bruto = self.cleaned_data.get("telefone", "")
        if not tel_bruto:
            return ""

        # Remove espaços, parênteses, hifens e caracteres especiais
        tel_limpo = re.sub(r"\D", "", str(tel_bruto))

        # Validação do formato brasileiro com DDD (10 ou 11 dígitos numéricos)
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

        # Validação mandatória da sala para Servidores
        if tipo == Perfil.TipoUsuario.SERVIDOR and not sala:
            self.add_error("sala_codigo", "É obrigatório associar uma sala para usuários do tipo Servidor.")

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["senha"])
        
        # Conecta a sala caso seja do tipo Servidor
        if self.cleaned_data.get("tipo") == Perfil.TipoUsuario.SERVIDOR:
            usuario.sala = self.cleaned_data.get("sala_codigo")
        else:
            usuario.sala = None

        if commit:
            usuario.save()
            # Vincula a instituição selecionada através do modelo intermediário
            instituicao = self.cleaned_data.get("instituicao_cnpj")
            if instituicao:
                VinculoInstituicao.objects.get_or_create(
                    perfil=usuario,
                    instituicao=instituicao
                    
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
        validar_cpf(cpf_limpo)  # Usa seu validador matemático do utils.py
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
        servidor.ativo = False          # Nasce bloqueado aguardando aprovação do Admin ou Servidor da unidade
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
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-custom", "placeholder": "Senha inicial"}),
        min_length=6,
        label="Senha Provisória"
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-custom", "placeholder": "Repita a senha"}),
        min_length=6,
        label="Confirmar Senha"
    )
    sala = forms.ModelChoiceField(
        queryset=Sala.objects.none(),
        required=False,
        empty_label="Selecione a sala de responsabilidade...",
        widget=forms.Select(attrs={"class": "form-select form-select-custom", "id": "id_sala"}),
        label="Sala Responsável"
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
            "nome": forms.TextInput(attrs={"class": "form-control form-control-custom", "placeholder": "Nome completo"}),
            "username": forms.TextInput(attrs={"class": "form-control form-control-custom", "placeholder": "nome.sobrenome"}),
            "cpf": forms.TextInput(attrs={"class": "form-control form-control-custom cpf-format", "placeholder": "000.000.000-00"}),
            "email": forms.EmailInput(attrs={"class": "form-control form-control-custom", "placeholder": "usuario@instituicao.edu.br"}),
            "telefone": forms.TextInput(attrs={"class": "form-control form-control-custom telefone-format", "placeholder": "(00) 00000-0000"}),
            "tipo": forms.Select(attrs={"class": "form-select form-select-custom", "id": "id_tipo"}),
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

        # 2. Filtra estritamente as salas da instituição ativa
        if self.instituicao:
            self.fields["sala"].queryset = Sala.objects.filter(
                instituicao=self.instituicao, 
                ativa=True
            ).order_by("predio", "nome")

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

        # Obriga a seleção de sala se for cadastrado como Servidor
        if tipo == Perfil.TipoUsuario.SERVIDOR and not sala:
            self.add_error("sala", "É obrigatório associar uma sala para perfis do tipo Servidor.")

        # Limpa o campo sala se for usuário comum
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
            # Vincula automaticamente à mesma instituição do servidor
            if self.instituicao:
                VinculoInstituicao.objects.get_or_create(
                    perfil=usuario,
                    instituicao=self.instituicao
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
            "sala": forms.Select(attrs={
                "class": "form-select form-select-custom",
            }),
        }

    def __init__(self, *args, instituicao=None, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Bloqueia alteração do e-mail no HTML e no processamento do Django
        self.fields["email"].disabled = True
        self.fields["email"].required = False

        # 2. Resolve a instituição vinculada (prioriza a instituição ativa passada pela view)
        if instituicao is None and self.instance and self.instance.pk:
            instituicao = self.instance.instituicao.filter(ativo=True).first()

        # 3. Filtra o select de salas apenas para as salas ativas da instituição do servidor
        if instituicao:
            self.fields["sala"].queryset = Sala.objects.filter(
                instituicao=instituicao,
                ativa=True,
            ).order_by("predio", "nome")
        else:
            self.fields["sala"].queryset = Sala.objects.none()

        self.fields["sala"].empty_label = "Selecione a sua sala/setor de atuação (Opcional)"

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
        # Ajuste os campos abaixo conforme os atributos exatos do seu model Perfil
        # Campos críticos como 'tipo', 'instituicao', 'ativo' ou 'matricula/siape' ficam fora para não serem editados pelo próprio servidor
        fields = [
            "telefone",
            "foto",
        ]
        widgets = {
            "telefone": forms.TextInput(attrs={"class": "form-control", "placeholder": "(86) 99999-9999", "id": "telefone"}),
            "foto": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }            