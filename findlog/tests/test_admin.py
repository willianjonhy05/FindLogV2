from django.test import RequestFactory, TestCase
from django.contrib.admin.sites import AdminSite
from unittest.mock import MagicMock

# Substitua 'seu_app' pelo nome real do seu app Django
from findlog.admin import (
    InstituicaoAdmin,
    CategoriaAdmin,
    SalaAdmin,
    PerfilAdmin,
    ItemAdmin,
    ReivindicacaoAdmin,
    ContatoAdmin,
)
from findlog.models import (
    Instituicao,
    Categoria,
    Sala,
    Perfil,
    Item,
    Reivindicacao,
    Contato,
)


class AdminTestCase(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()
        self.superuser = MagicMock(is_active=True, is_staff=True, is_superuser=True)

    def test_instituicao_admin_cnpj_exibicao(self):
        admin_inst = InstituicaoAdmin(Instituicao, self.site)
        obj = MagicMock(cnpj_formatado="12.345.678/0001-95")
        self.assertEqual(admin_inst.cnpj_exibicao(obj), "12.345.678/0001-95")

    def test_perfil_admin_cpf_exibicao(self):
        admin_perfil = PerfilAdmin(Perfil, self.site)
        obj = MagicMock(cpf_formatado="123.456.789-01")
        self.assertEqual(admin_perfil.cpf_exibicao(obj), "123.456.789-01")

    def test_perfil_admin_idade_exibicao(self):
        admin_perfil = PerfilAdmin(Perfil, self.site)
        
        # Com idade informada
        obj_com_idade = MagicMock(idade=30)
        self.assertEqual(admin_perfil.idade_exibicao(obj_com_idade), "30 anos")
        
        # Sem idade informada (None)
        obj_sem_idade = MagicMock(idade=None)
        self.assertEqual(admin_perfil.idade_exibicao(obj_sem_idade), "-")

    def test_perfil_admin_miniatura_e_preview_foto(self):
        admin_perfil = PerfilAdmin(Perfil, self.site)
        
        # Objeto sem foto
        obj_sem_foto = MagicMock(foto=None)
        self.assertEqual(admin_perfil.miniatura_foto(obj_sem_foto), "-")
        self.assertEqual(admin_perfil.preview_foto(obj_sem_foto), "Sem foto anexada")

        # Objeto com foto
        obj_com_foto = MagicMock()
        obj_com_foto.foto.url = "/media/fotos/perfil.jpg"
        
        html_miniatura = admin_perfil.miniatura_foto(obj_com_foto)
        self.assertIn("/media/fotos/perfil.jpg", html_miniatura)
        self.assertIn("object-fit: cover", html_miniatura)

        html_preview = admin_perfil.preview_foto(obj_com_foto)
        self.assertIn("/media/fotos/perfil.jpg", html_preview)
        self.assertIn("max-height: 180px", html_preview)

    def test_item_admin_miniatura_e_preview_foto(self):
        admin_item = ItemAdmin(Item, self.site)
        
        # Objeto sem foto
        obj_sem_foto = MagicMock(foto=None)
        self.assertEqual(admin_item.miniatura_foto(obj_sem_foto), "-")
        self.assertEqual(admin_item.preview_foto(obj_sem_foto), "Sem foto anexada")

        # Objeto com foto
        obj_com_foto = MagicMock()
        obj_com_foto.foto.url = "/media/itens/chave.jpg"
        
        html_miniatura = admin_item.miniatura_foto(obj_com_foto)
        self.assertIn("/media/itens/chave.jpg", html_miniatura)

        html_preview = admin_item.preview_foto(obj_com_foto)
        self.assertIn("/media/itens/chave.jpg", html_preview)
        self.assertIn("max-height: 220px", html_preview)

    def test_contato_admin_permissions(self):
        admin_contato = ContatoAdmin(Contato, self.site)
        request = self.factory.get("/admin/")
        request.user = self.superuser

        # Verifica se as permissões personalizadas bloqueiam adição e alteração
        self.assertFalse(admin_contato.has_add_permission(request))
        self.assertFalse(admin_contato.has_change_permission(request, obj=None))