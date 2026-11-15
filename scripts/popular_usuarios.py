import os
import sys
from datetime import date
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")  # Ajuste "setup.settings" se necessário
django.setup()

from findlog.models import Instituicao, Perfil, Sala, VinculoInstituicao


SENHA_PADRAO = "Teste@123"


def gerar_cpf_valido(semente_numerica):
    """Gera um CPF de 11 dígitos matematicamente válido a partir de um número base."""
    base = f"{semente_numerica:09d}"[-9:]
    # Garante que não seja sequência repetida (ex: 111111111)
    if len(set(base)) == 1:
        base = base[:-1] + str((int(base[-1]) + 1) % 10)

    numeros = [int(d) for d in base]

    # Primeiro dígito verificador
    soma1 = sum(numeros[i] * (10 - i) for i in range(9))
    dig1 = (soma1 * 10) % 11
    dig1 = 0 if dig1 == 10 else dig1
    numeros.append(dig1)

    # Segundo dígito verificador
    soma2 = sum(numeros[i] * (11 - i) for i in range(10))
    dig2 = (soma2 * 10) % 11
    dig2 = 0 if dig2 == 10 else dig2
    numeros.append(dig2)

    return "".join(str(d) for d in numeros)


# 30 perfis: 20 Usuários Comuns + 10 Servidores
USUARIOS_DADOS = [
    # --- 20 USUÁRIOS COMUNS ---
    ("Ana Beatriz Alves", "ana.alves@teste.com", "86991000001", "20241001", date(2002, 3, 14), Perfil.TipoUsuario.USUARIO, True, False),
    ("Bruno Henrique Lima", "bruno.lima@teste.com", "86991000002", "20241002", date(2001, 7, 22), Perfil.TipoUsuario.USUARIO, True, True),  # Multi-instituição
    ("Camila Sousa Rocha", "camila.rocha@teste.com", "86991000003", "20241003", date(2003, 11, 5), Perfil.TipoUsuario.USUARIO, True, False),
    ("Daniel Costa Martins", "daniel.martins@teste.com", "86991000004", "20241004", date(2000, 1, 30), Perfil.TipoUsuario.USUARIO, True, True),  # Multi-instituição
    ("Eduarda Pereira Silva", "eduarda.silva@teste.com", "86991000005", "20241005", date(2004, 5, 19), Perfil.TipoUsuario.USUARIO, True, False),
    ("Fábio Oliveira Santos", "fabio.santos@teste.com", "86991000006", "20241006", date(1999, 9, 8), Perfil.TipoUsuario.USUARIO, True, False),
    ("Gabriela Ferreira Mendes", "gabriela.mendes@teste.com", "86991000007", "20241007", date(2002, 12, 2), Perfil.TipoUsuario.USUARIO, True, True),  # Multi-instituição
    ("Hugo Nascimento Gomes", "hugo.gomes@teste.com", "86991000008", "20241008", date(2001, 4, 27), Perfil.TipoUsuario.USUARIO, True, False),
    ("Isabela Ribeiro Castro", "isabela.castro@teste.com", "86991000009", "20241009", date(2003, 8, 11), Perfil.TipoUsuario.USUARIO, True, False),
    ("João Pedro Carvalho", "joao.carvalho@teste.com", "86991000010", "20241010", date(2000, 6, 16), Perfil.TipoUsuario.USUARIO, True, False),
    ("Karina Rodrigues Dias", "karina.dias@teste.com", "86991000011", "20241011", date(2002, 2, 25), Perfil.TipoUsuario.USUARIO, True, False),
    ("Leonardo Barbosa Moura", "leonardo.moura@teste.com", "86991000012", "20241012", date(1998, 10, 3), Perfil.TipoUsuario.USUARIO, True, False),
    ("Mariana Teixeira Araújo", "mariana.araujo@teste.com", "86991000013", "20241013", date(2004, 1, 17), Perfil.TipoUsuario.USUARIO, True, False),
    ("Natália Moreira Pinto", "natalia.pinto@teste.com", "86991000014", "20241014", date(2001, 9, 29), Perfil.TipoUsuario.USUARIO, True, False),
    ("Otávio Cardoso Freitas", "otavio.freitas@teste.com", "86991000015", "20241015", date(2003, 4, 6), Perfil.TipoUsuario.USUARIO, True, False),
    ("Paula Fernandes Correia", "paula.correia@teste.com", "86991000016", "20241016", date(2000, 12, 21), Perfil.TipoUsuario.USUARIO, True, False),
    ("Rafael Monteiro Vieira", "rafael.vieira@teste.com", "86991000017", "20241017", date(2002, 7, 9), Perfil.TipoUsuario.USUARIO, True, False),
    ("Sabrina Azevedo Cunha", "sabrina.cunha@teste.com", "86991000018", "20241018", date(2001, 11, 13), Perfil.TipoUsuario.USUARIO, True, False),
    ("Tiago Cavalcante Borges", "tiago.borges@teste.com", "86991000019", "20241019", date(1999, 3, 28), Perfil.TipoUsuario.USUARIO, False, False),  # Usuário inativo
    ("Vitória Machado Nogueira", "vitoria.nogueira@teste.com", "86991000020", "20241020", date(2003, 6, 4), Perfil.TipoUsuario.USUARIO, True, False),

    # --- 10 SERVIDORES ---
    ("Marcos Vinícius Sousa", "marcos.servidor@teste.com", "86992000001", "SIAPE1001", date(1985, 5, 12), Perfil.TipoUsuario.SERVIDOR, True, True),   # Servidor multi-instituição
    ("Cláudia Regina Barros", "claudia.servidor@teste.com", "86992000002", "SIAPE1002", date(1988, 8, 24), Perfil.TipoUsuario.SERVIDOR, True, False),
    ("Roberto Carlos Lima", "roberto.servidor@teste.com", "86992000003", "SIAPE1003", date(1990, 2, 10), Perfil.TipoUsuario.SERVIDOR, True, False),
    ("Patrícia Gomes Alencar", "patricia.servidor@teste.com", "86992000004", "SIAPE1004", date(1983, 11, 18), Perfil.TipoUsuario.SERVIDOR, True, True),  # Servidor multi-instituição
    ("Anderson Silva Tavares", "anderson.servidor@teste.com", "86992000005", "SIAPE1005", date(1992, 4, 7), Perfil.TipoUsuario.SERVIDOR, True, False),
    ("Juliana Melo Vasconcelos", "juliana.servidor@teste.com", "86992000006", "SIAPE1006", date(1987, 9, 15), Perfil.TipoUsuario.SERVIDOR, True, False),
    ("Fernando Brito Sampaio", "fernando.servidor@teste.com", "86992000007", "SIAPE1007", date(1981, 12, 30), Perfil.TipoUsuario.SERVIDOR, True, False),
    ("Renata Soares Queiroz", "renata.servidor@teste.com", "86992000008", "SIAPE1008", date(1994, 6, 20), Perfil.TipoUsuario.SERVIDOR, False, False),  # Pendente de aprovação
    ("Gustavo Farias Bezerra", "gustavo.servidor@teste.com", "86992000009", "SIAPE1009", date(1989, 1, 9), Perfil.TipoUsuario.SERVIDOR, False, False),   # Pendente de aprovação
    ("Luciana Duarte Miranda", "luciana.servidor@teste.com", "86992000010", "SIAPE1010", date(1986, 10, 26), Perfil.TipoUsuario.SERVIDOR, True, False),
]


def executar():
    instituicoes = list(Instituicao.objects.filter(ativo=True).order_by("nome"))

    if not instituicoes:
        print("[!] Nenhuma instituição ativa encontrada. Execute 'popular_instituicoes.py' primeiro.")
        return

    criados = 0
    existentes = 0

    for idx, dados in enumerate(USUARIOS_DADOS, start=1):
        nome, email, telefone, codigo, nascimento, tipo, ativo, multi_inst = dados
        cpf = gerar_cpf_valido(100200300 + idx)

        # Distribui entre as instituições disponíveis
        inst_principal = instituicoes[(idx - 1) % len(instituicoes)]

        # Se for servidor, vincula a uma sala ativa da instituição principal (se existir)
        sala_vinculada = None
        if tipo == Perfil.TipoUsuario.SERVIDOR:
            sala_vinculada = Sala.objects.filter(instituicao=inst_principal, ativa=True).first()

        perfil, criado = Perfil.objects.get_or_create(
            email=email,
            defaults={
                "nome": nome,
                "cpf": cpf,
                "telefone": telefone,
                "codigo": codigo,
                "data_nascimento": nascimento,
                "tipo": tipo,
                "sala": sala_vinculada,
                "ativo": ativo,
                "is_staff": False,
                "is_superuser": False,
            },
        )

        if criado:
            perfil.set_password(SENHA_PADRAO)
            perfil.save(update_fields=["password"])

            # Vincula à instituição principal
            VinculoInstituicao.objects.get_or_create(
                perfil=perfil,
                instituicao=inst_principal,
            )

            # Se marcado como multi-instituição e houver mais de 1 instituição, vincula à segunda também
            if multi_inst and len(instituicoes) > 1:
                inst_secundaria = instituicoes[idx % len(instituicoes)]
                VinculoInstituicao.objects.get_or_create(
                    perfil=perfil,
                    instituicao=inst_secundaria,
                )

            criados += 1
            papel = "Servidor" if tipo == Perfil.TipoUsuario.SERVIDOR else "Usuário"
            status_txt = "Ativo" if ativo else "Inativo/Pendente"
            extra_txt = " [Multi-Instituição]" if (multi_inst and len(instituicoes) > 1) else ""
            print(f"[+] {papel} criado: {perfil.nome} ({email}) | {status_txt}{extra_txt}")
        else:
            existentes += 1
            print(f"[=] Já existia: {perfil.nome} ({email})")

    print(f"\nResumo Usuários -> Criados: {criados} | Já existentes: {existentes}")
    print(f"Senha padrão para todos os perfis criados: {SENHA_PADRAO}")


if __name__ == "__main__":
    executar()