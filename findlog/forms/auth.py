from django import forms
from django.contrib.auth import authenticate

import re

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



class EsqueciSenhaForm(forms.Form):
    identificador = forms.CharField(
        label="E-mail ou CPF",
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Digite seu e-mail cadastrado ou CPF",
                "autocomplete": "username",
                "required": True,
            }
        ),
    )

    def clean_identificador(self):
        dado = self.cleaned_data.get("identificador", "").strip()
        # Se contiver apenas dígitos ou máscara de CPF, limpa pontuações
        apenas_num = re.sub(r"\D", "", dado)
        if len(apenas_num) == 11 and "@" not in dado:
            return apenas_num
        return dado.lower()        
