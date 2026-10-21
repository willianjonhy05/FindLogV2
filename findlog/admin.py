from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Instituicao,
    Categoria,
    Sala,
    Perfil,
    VinculoInstituicao,
    Item,
    Reivindicacao,
    Contato,
)


# ==============================================================================
# INLINES
# ==============================================================================

class VinculoInstituicaoInline(admin.TabularInline):
    model = VinculoInstituicao
    extra = 1
    autocomplete_fields = ["instituicao"]


class ReivindicacaoItemInline(admin.StackedInline):
    model = Reivindicacao
    extra = 0
    show_change_link = True
    fields = ("protocolo", "autor", "status", "data", "data_devolucao")
    readonly_fields = ("protocolo", "data")
    can_delete = False


# ==============================================================================
# ADMIN MODELS
# ==============================================================================

@admin.register(Instituicao)
class InstituicaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj_exibicao", "telefone_formatado", "email", "ativo", "data_criacao")
    list_filter = ("ativo", "data_criacao")
    search_fields = ("nome", "cnpj", "email")
    readonly_fields = ("data_criacao", "cnpj_formatado", "telefone_formatado")
    fieldsets = (
        ("Identificação", {
            "fields": ("nome", "cnpj", "cnpj_formatado", "ativo")
        }),
        ("Contato e Localização", {
            "fields": ("endereco", "telefone", "telefone_formatado", "email")
        }),
        ("Metadados", {
            "fields": ("data_criacao",),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="CNPJ")
    def cnpj_exibicao(self, obj):
        return obj.cnpj_formatado


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "slug", "ativa")
    list_filter = ("ativa",)
    search_fields = ("nome", "codigo", "slug")
    readonly_fields = ("codigo", "slug")
    fieldsets = (
        ("Informações Principais", {
            "fields": ("codigo", "nome", "slug", "ativa")
        }),
        ("Detalhes", {
            "fields": ("descricao",)
        }),
    )


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "instituicao", "predio", "andar", "sala_de_aula", "laboratorio", "ativa")
    list_filter = ("ativa", "sala_de_aula", "laboratorio", "predio", "instituicao")
    search_fields = ("nome", "codigo", "descricao")
    autocomplete_fields = ["instituicao"]
    readonly_fields = ("codigo", "telefone_formatado")
    fieldsets = (
        ("Localização", {
            "fields": ("codigo", "nome", "instituicao", "predio", "andar")
        }),
        ("Classificação e Status", {
            "fields": ("sala_de_aula", "laboratorio", "ativa")
        }),
        ("Contato e Detalhes", {
            "fields": ("telefone", "telefone_formatado", "descricao")
        }),
    )


@admin.register(Perfil)
class PerfilAdmin(UserAdmin):
    inlines = [VinculoInstituicaoInline]
    list_display = ("username", "nome", "email", "tipo", "cpf_exibicao", "idade_exibicao", "ativo", "miniatura_foto")
    list_filter = ("tipo", "ativo", "is_staff", "is_superuser")
    search_fields = ("username", "nome", "email", "cpf", "codigo")
    autocomplete_fields = ["sala"]
    readonly_fields = ("criado_em", "last_login", "date_joined", "idade_exibicao", "cpf_formatado", "telefone_formatado", "preview_foto")
    ordering = ("nome", "email")

    fieldsets = (
        ("Credenciais", {
            "fields": ("username", "password")
        }),
        ("Dados Pessoais", {
            "fields": ("nome", "email", "cpf", "cpf_formatado", "data_nascimento", "idade_exibicao", "telefone", "telefone_formatado", "foto", "preview_foto")
        }),
        ("Função Institucional", {
            "fields": ("tipo", "codigo", "sala", "ativo")
        }),
        ("Permissões do Sistema", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",)
        }),
        ("Datas de Acesso", {
            "fields": ("criado_em", "last_login", "date_joined"),
            "classes": ("collapse",)
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "cpf", "password", "tipo"),
        }),
    )

    @admin.display(description="CPF")
    def cpf_exibicao(self, obj):
        return obj.cpf_formatado

    @admin.display(description="Idade")
    def idade_exibicao(self, obj):
        return f"{obj.idade} anos" if obj.idade is not None else "-"

    @admin.display(description="Foto")
    def miniatura_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="width: 36px; height: 36px; object-fit: cover; border-radius: 50%;" />', obj.foto.url)
        return "-"

    @admin.display(description="Visualização da Foto")
    def preview_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="max-height: 180px; border-radius: 8px;" />', obj.foto.url)
        return "Sem foto anexada"


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    inlines = [ReivindicacaoItemInline]
    list_display = ("codigo", "nome", "categoria", "instituicao", "status", "data_registro", "miniatura_foto")
    list_filter = ("status", "categoria", "instituicao", "data_registro")
    search_fields = ("codigo", "nome", "marca_ou_modelo", "descricao")
    autocomplete_fields = ["categoria", "instituicao", "usuario_registro", "dono", "local", "local_guardado"]
    readonly_fields = ("uuid", "codigo", "data_registro", "preview_foto")
    date_hierarchy = "data_registro"

    fieldsets = (
        ("Identificação do Item", {
            "fields": ("uuid", "codigo", "status", "nome", "categoria", "instituicao")
        }),
        ("Características Físicas", {
            "fields": ("marca_ou_modelo", "tamanho", "cor", "material", "descricao", "foto", "preview_foto")
        }),
        ("Rastreamento e Pessoas", {
            "fields": ("local", "local_guardado", "usuario_registro", "dono")
        }),
        ("Prazos", {
            "fields": ("data_registro", "data_devolucao")
        }),
    )

    @admin.display(description="Foto")
    def miniatura_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;" />', obj.foto.url)
        return "-"

    @admin.display(description="Foto do Item")
    def preview_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="max-height: 220px; border-radius: 6px;" />', obj.foto.url)
        return "Sem foto anexada"


@admin.register(Reivindicacao)
class ReivindicacaoAdmin(admin.ModelAdmin):
    list_display = ("protocolo", "item", "autor", "instituicao", "status", "data", "responsavel_admin")
    list_filter = ("status", "instituicao", "data")
    search_fields = ("protocolo", "pedido", "resposta_admin", "autor__nome", "autor__email", "item__codigo")
    autocomplete_fields = ["autor", "item", "instituicao", "responsavel_admin", "local_devolucao"]
    readonly_fields = ("protocolo", "data")
    date_hierarchy = "data"

    fieldsets = (
        ("Cabeçalho da Solicitação", {
            "fields": ("protocolo", "data", "status", "instituicao", "item", "autor")
        }),
        ("Detalhes do Pedido", {
            "fields": ("pedido", "anexos")
        }),
        ("Despacho e Devolução", {
            "fields": ("responsavel_admin", "resposta_admin", "local_devolucao", "data_devolucao")
        }),
    )


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = (
        "assunto",
        "nome",
        "email",
        "telefone_formatado",
        "data",
        "ip_contato",
    )
    list_filter = ("assunto", "data")  # Adicionar 'assunto' ao filtro ajuda bastante
    search_fields = ("nome", "email", "telefone", "assunto", "mensagem", "ip_contato")
    readonly_fields = (
        "uuid",
        "nome",
        "email",
        "telefone",
        "telefone_formatado",
        "assunto",
        "mensagem",
        "data",
        "ip_contato",
    )
    date_hierarchy = "data"

    fieldsets = (
        ("Remetente", {
            "fields": (
                "uuid",
                "nome",
                "email",
                ("telefone", "telefone_formatado"),  # Ficam lado a lado na mesma linha
                "ip_contato",
            )
        }),
        ("Conteúdo", {
            "fields": ("assunto", "mensagem", "data")
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Impede alterações acidentais nas mensagens recebidas
        return False