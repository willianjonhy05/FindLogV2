from django import forms
from ..models import Instituicao, Sala
from ..utils import apenas_digitos

import re

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
            "telefone",
            "descricao",
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
            "telefone": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "(00) 0000-0000",
                "id": "telefone",
            }),
            "descricao": forms.Textarea(attrs={
                "class": "form-control form-control-custom",
                "rows": 3,
                "placeholder": "Detalhes adicionais sobre a sala...",
                "id": "descricao",
            }),
            "laboratorio": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "laboratorio"}),
            "sala_de_aula": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "sala_de_aula"}),
            "ativa": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "ativa"}),
        }

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone", "")
        return apenas_digitos(telefone) if telefone else ""



class ServidorSalaForm(forms.ModelForm):
    class Meta:
        model = Sala
        fields = [
            "nome",
            "predio",
            "andar",
            "telefone",
            "descricao",
            "sala_de_aula",
            "laboratorio",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Laboratório de Redes, Sala 102",
                "required": True,
            }),
            "predio": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Bloco A, Central",
                "required": True,
            }),
            "andar": forms.TextInput(attrs={
                "class": "form-control form-control-custom",
                "placeholder": "Ex: Térreo, 1º",
                "required": True,
            }),
            "telefone": forms.TextInput(attrs={
                "class": "form-control form-control-custom telefone-format",
                "placeholder": "(00) 00000-0000",
            }),
            "descricao": forms.Textarea(attrs={
                "class": "form-control form-control-custom",
                "rows": 3,
                "placeholder": "Detalhes de localização, pontos de referência...",
            }),
            "sala_de_aula": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "laboratorio": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone", "")
        if not telefone:
            return ""
        return re.sub(r"\D", "", str(telefone))            



class ServidorUpdateSalaForm(forms.ModelForm):
    class Meta:
        model = Sala
        fields = [
            'nome',
            'predio',
            'andar',
            'telefone',
            'sala_de_aula',
            'laboratorio',
            'descricao',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'id': 'id_nome',
                'placeholder': 'Ex: Sala 101, Auditório Principal',
            }),
            'predio': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'id': 'id_predio',
                'maxlength': '5',
                'placeholder': 'Ex: A, B, Bloco 1',
            }),
            'andar': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'id': 'id_andar',
                'maxlength': '5',
                'placeholder': 'Ex: Térreo, 1º',
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'id': 'id_telefone',
                'placeholder': 'Ex: (86) 3215-0000',
            }),
            'sala_de_aula': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_sala_de_aula',
            }),
            'laboratorio': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_laboratorio',
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control form-control-custom',
                'id': 'id_descricao',
                'rows': 3,
                'placeholder': 'Ponto de referência, capacidade de alunos, recursos...',
            }),
        }

    # def clean_nome(self):
    #     nome = self.cleaned_data.get('nome')
    #     instituicao = self.instance.instituicao

    #     # Garante unicidade do nome dentro da mesma instituição excluindo a própria instância
    #     duplicada = Sala.objects.filter(
    #         instituicao=instituicao,
    #         nome__iexact=nome
    #     ).exclude(pk=self.instance.pk).exists()

    #     if duplicada:
    #         raise forms.ValidationError('Já existe uma sala cadastrada com este nome nesta unidade.')
    #     return nome


    
