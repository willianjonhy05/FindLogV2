from django.test import TestCase
from findlog.models import Perfil, Instituicao, Sala, VinculoInstituicao
from findlog.forms.perfil import (  # Ajuste o import para o local onde esses forms estão salvos
    NovoUsuarioForm,
    AutoCadastroUsuarioForm,
    AutoCadastroServidorForm,
    ServidorCadastroColegaForm,
    EditarMeuPerfilForm,
    TrocarMinhaSenhaForm,
)


class UserFormsTestCase(TestCase):

    def setUp(self):
        self.instituicao = Instituicao.objects.create(
            cnpj="12345678000195",
            nome="IFPI Campus Teresina Central",
            endereco="Centro",
            email="teresina@ifpi.edu.br",
            ativo=True
        )
        self.sala_servidor = Sala.objects.create(
            instituicao=self.instituicao,
            predio="Bloco A",
            andar="1º",
            nome="Secretaria",
            ativa=True
        )
        self.usuario_comum = Perfil.objects.create_user(
            username="usuario_base",
            email="base@exemplo.com",
            password="senha123",
            cpf="11144477735",
            nome="Usuário Base"
        )

    # ==========================================
    # Testes para o NovoUsuarioForm
    # ==========================================
    def test_novo_usuario_form_servidor_exige_sala(self):
        """Testa se o formulário exige sala quando o tipo de usuário selecionado é Servidor."""
        form_data = {
            "nome": "Novo Servidor",
            "cpf": "03854892004",
            "email": "servidor@ifpi.edu.br",
            "senha": "senha123",
            "confirmar_senha": "senha123",
            "tipo": Perfil.TipoUsuario.SERVIDOR,
            "instituicao_cnpj": self.instituicao.cnpj,
            "sala_codigo": "",  # Vazio propositalmente
        }
        form = NovoUsuarioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("sala_codigo", form.errors)

    def test_novo_usuario_form_valido_como_usuario(self):
        """Testa a criação bem-sucedida de um usuário comum com vínculo institucional."""
        form_data = {
            "nome": "Novo Aluno",
            "cpf": "46718442062",
            "email": "aluno@ifpi.edu.br",
            "senha": "senha123",
            "confirmar_senha": "senha123",
            "tipo": Perfil.TipoUsuario.USUARIO,
            "instituicao_cnpj": self.instituicao.cnpj,
        }
        form = NovoUsuarioForm(data=form_data)
        self.assertTrue(form.is_valid())
        perfil = form.save()
        
        self.assertEqual(perfil.tipo, Perfil.TipoUsuario.USUARIO)
        self.assertTrue(VinculoInstituicao.objects.filter(perfil=perfil, instituicao=self.instituicao).exists())

    # ==========================================
    # Testes para o AutoCadastroUsuarioForm
    # ==========================================
    def test_auto_cadastro_usuario_valido(self):
        """Testa o autocadastro público de um usuário comum."""
        form_data = {
            "nome": "Autocadastro Aluno",
            "email": "autocadastro@exemplo.com",
            "cpf": "20715520083",
            "telefone": "(86) 98888-7766",
            "senha": "senha123",
            "confirmar_senha": "senha123",
        }
        form = AutoCadastroUsuarioForm(data=form_data, instituicao=self.instituicao)
        self.assertTrue(form.is_valid())
        usuario = form.save()
        
        self.assertEqual(usuario.tipo, Perfil.TipoUsuario.USUARIO)
        self.assertTrue(usuario.ativo)
        self.assertTrue(VinculoInstituicao.objects.filter(perfil=usuario, instituicao=self.instituicao).exists())

    def test_auto_cadastro_email_duplicado(self):
        """Testa se o autocadastro bloqueia e-mails já cadastrados no sistema."""
        form_data = {
            "nome": "Outro Aluno",
            "email": "base@exemplo.com",  # E-mail já existente no setUp
            "cpf": "74358654002",
            "senha": "senha123",
            "confirmar_senha": "senha123",
        }
        form = AutoCadastroUsuarioForm(data=form_data, instituicao=self.instituicao)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    # ==========================================
    # Testes para o AutoCadastroServidorForm
    # ==========================================
    def test_auto_cadastro_servidor_valido(self):
        """Testa o autocadastro de servidor (nasce inativo/bloqueado aguardando aprovação)."""
        form_data = {
            "nome": "Novo Servidor Público",
            "email": "servidor.publico@ifpi.edu.br",
            "cpf": "36076654007",
            "senha": "senha123",
            "confirmar_senha": "senha123",
            "sala": self.sala_servidor.pk,
        }
        form = AutoCadastroServidorForm(data=form_data, instituicao=self.instituicao)
        self.assertTrue(form.is_valid())
        servidor = form.save()
        
        self.assertEqual(servidor.tipo, Perfil.TipoUsuario.SERVIDOR)
        self.assertFalse(servidor.ativo)  # Aguardando aprovação
        self.assertEqual(servidor.sala, self.sala_servidor)


    def test_cadastro_rejeita_cpf_invalido(self):
        """Testa se o formulário rejeita CPFs com dígitos verificadores incorretos ou inválidos."""
        form_data = {
            "nome": "Usuário CPF Falso",
            "email": "cpffalso@exemplo.com",
            "cpf": "123.456.789-01",  # CPF inválido matematicamente
            "senha": "senha123",
            "confirmar_senha": "senha123",
        }
        form = AutoCadastroUsuarioForm(data=form_data, instituicao=self.instituicao)
        
        # O formulário deve ser inválido
        self.assertFalse(form.is_valid())
        # O erro deve estar localizado no campo 'cpf'
        self.assertIn("cpf", form.errors)        

    # ==========================================
    # Testes para o ServidorCadastroColegaForm
    # ==========================================
    def test_servidor_cadastro_colega_valido(self):
        """Testa o cadastro de um colega feito por um servidor."""
        form_data = {
            "nome": "Colega Servidor",
            "username": "colega.servidor",
            "cpf": "06239480010",
            "email": "colega@ifpi.edu.br",
            "tipo": Perfil.TipoUsuario.SERVIDOR,
            "sala": f"{self.sala_servidor.nome} - {self.sala_servidor.predio}",  # Datalist espera "Secretaria - Bloco A"
            "senha": "senha123",
            "confirmar_senha": "senha123",
        }
        form = ServidorCadastroColegaForm(data=form_data, instituicao=self.instituicao)
        self.assertTrue(form.is_valid(), msg=form.errors)
        novo_colega = form.save()
        
        self.assertTrue(novo_colega.ativo)
        self.assertEqual(novo_colega.sala, self.sala_servidor)

    # ==========================================
    # Testes para o EditarMeuPerfilForm
    # ==========================================
    def test_editar_meu_perfil_valido(self):
        """Testa a edição de dados básicos do próprio perfil."""
        form_data = {
            "nome": "Usuário Base Atualizado",
            "email": "base.atualizado@exemplo.com",
            "telefone": "(86) 91111-2222",
        }
        form = EditarMeuPerfilForm(data=form_data, instance=self.usuario_comum)
        self.assertTrue(form.is_valid())
        perfil_atualizado = form.save()
        
        self.assertEqual(perfil_atualizado.nome, "Usuário Base Atualizado")
        self.assertEqual(perfil_atualizado.email, "base.atualizado@exemplo.com")

    # ==========================================
    # Testes para o TrocarMinhaSenhaForm
    # ==========================================
    def test_trocar_minha_senha_valida(self):
        """Testa a alteração de senha utilizando o PasswordChangeForm do Django."""
        form_data = {
            "old_password": "senha123",
            "new_password1": "novaSenhaSegura456",
            "new_password2": "novaSenhaSegura456",
        }
        form = TrocarMinhaSenhaForm(user=self.usuario_comum, data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        
        # Verifica se a senha foi alterada com sucesso autenticando novamente
        self.assertTrue(self.usuario_comum.check_password("novaSenhaSegura456"))