from django import forms
from ..models import Instituicao

import re

class InstituicaoForm(forms.ModelForm):
    ativo = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input custom-switch"})
    )

    class Meta:
        model = Instituicao
        fields = ["cnpj", "nome", "endereco", "telefone", "email", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control form-control-custom", "placeholder": "Nome do campus"}),
            "cnpj": forms.TextInput(attrs={"class": "form-control form-control-custom cnpj-format", "placeholder": "00.000.000/0000-00"}),
            "endereco": forms.TextInput(attrs={"class": "form-control form-control-custom", "placeholder": "Endereço completo"}),
            "telefone": forms.TextInput(attrs={"class": "form-control form-control-custom telefone-format", "placeholder": "(00) 00000-0000"}),
            "email": forms.EmailInput(attrs={"class": "form-control form-control-custom", "placeholder": "contato@instituicao.edu.br"}),
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get("cnpj", "")
        cnpj_limpo = re.sub(r"\D", "", str(cnpj))
        if Instituicao.objects.filter(pk=cnpj_limpo).exists():
            raise forms.ValidationError("Já existe uma instituição cadastrada com este CNPJ.")
        return cnpj_limpo

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone", "")
        if not telefone:
            return ""
        return re.sub(r"\D", "", str(telefone))

class InstituicaoUpdateForm(forms.ModelForm):
    class Meta:
        model = Instituicao
        fields = ["nome", "endereco", "telefone", "email", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control form-control-custom"}),
            "endereco": forms.TextInput(attrs={"class": "form-control form-control-custom"}),
            "telefone": forms.TextInput(attrs={"class": "form-control form-control-custom telefone-format"}),
            "email": forms.EmailInput(attrs={"class": "form-control form-control-custom"}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input custom-switch"}),
        }

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone", "")
        if not telefone:
            return ""

        # Remove tudo que não for dígito numérico (espaços, parênteses, traços, etc.)
        telefone_limpo = re.sub(r"\D", "", str(telefone))
        
        # Opcional: validação básica de quantidade de dígitos para telefones brasileiros (10 ou 11)
        if telefone_limpo and len(telefone_limpo) not in (10, 11):
            raise forms.ValidationError("Informe um número de telefone válido com DDD (10 ou 11 dígitos).")

        return telefone_limpo

