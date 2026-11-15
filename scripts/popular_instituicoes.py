import os
import sys
import django

# Configura o ambiente do Django para execução direta via terminal
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")  # Ajuste "setup.settings" se necessário
django.setup()

from findlog.models import Instituicao


INSTITUICOES_DADOS = [
    {
        "cnpj": "11222333000181",
        "nome": "IFPI - Campus Teresina Central",
        "endereco": "Praça da Liberdade, 1597 - Centro, Teresina - PI",
        "telefone": "8631311400",
        "email": "achados.catcentral@ifpi.edu.br",
        "ativo": True,
    },
    {
        "cnpj": "22333444000192",
        "nome": "IFPI - Campus Teresina Zona Sul",
        "endereco": "Av. Pedro Freitas, 1020 - São Pedro, Teresina - PI",
        "telefone": "8631311500",
        "email": "achados.catzs@ifpi.edu.br",
        "ativo": True,
    },
    {
        "cnpj": "33444555000103",
        "nome": "UFPI - Campus Ministro Petrônio Portella",
        "endereco": "Av. Universitária, s/n - Ininga, Teresina - PI",
        "telefone": "8632155511",
        "email": "protocolo.ininga@ufpi.edu.br",
        "ativo": True,
    },
    {
        "cnpj": "44555666000114",
        "nome": "UESPI - Campus Poeta Torquato Neto",
        "endereco": "Rua João Cabral, 2231 - Pirajá, Teresina - PI",
        "telefone": "8632137126",
        "email": "secretaria.geral@uespi.br",
        "ativo": True,
    },
    {
        "cnpj": "55666777000125",
        "nome": "Senac Piauí - Unidade Centro",
        "endereco": "Av. Campos Sales, 1111 - Centro, Teresina - PI",
        "telefone": "8632289500",
        "email": "atendimento.centro@pi.senac.br",
        "ativo": True,
    },
    {
        "cnpj": "66777888000136",
        "nome": "Sesc Cajuína - Centro Cultural",
        "endereco": "Av. Cajuína, 725 - Noivos, Teresina - PI",
        "telefone": "8632309900",
        "email": "recepcao.cajuina@pi.sesc.com.br",
        "ativo": True,
    },
    {
        "cnpj": "77888999000147",
        "nome": "Hospital Universitário do Piauí (HU-UFPI)",
        "endereco": "Av. Universitária, s/n - Ininga, Teresina - PI",
        "telefone": "8632285200",
        "email": "ouvidoria.hu@ufpi.edu.br",
        "ativo": True,
    },
    {
        "cnpj": "88999000000158",
        "nome": "Biblioteca Pública Estadual Cromwell de Carvalho",
        "endereco": "Praça Demóstenes Avelino, s/n - Centro, Teresina - PI",
        "telefone": "8632214011",
        "email": "acervo@cultura.pi.gov.br",
        "ativo": True,
    },
    {
        "cnpj": "99000111000169",
        "nome": "Centro Administrativo Estadual - Bloco I",
        "endereco": "Av. Antonino Freire, 1450 - Centro, Teresina - PI",
        "telefone": "8632162000",
        "email": "portaria.bloco1@sead.pi.gov.br",
        "ativo": True,
    },
    {
        "cnpj": "12345678000195",
        "nome": "Unidade Experimental de Testes (Inativa)",
        "endereco": "Rua Coelho Rodrigues, 500 - Centro, Teresina - PI",
        "telefone": "86999990000",
        "email": "teste.inativo@findlog.com.br",
        "ativo": False,
    },
]


def executar():
    criadas = 0
    existentes = 0

    for dados in INSTITUICOES_DADOS:
        inst, criada = Instituicao.objects.get_or_create(
            cnpj=dados["cnpj"],
            defaults={
                "nome": dados["nome"],
                "endereco": dados["endereco"],
                "telefone": dados["telefone"],
                "email": dados["email"],
                "ativo": dados["ativo"],
            },
        )
        if criada:
            criadas += 1
            print(f"[+] Instituição criada: {inst.nome}")
        else:
            existentes += 1
            print(f"[=] Já existia: {inst.nome}")

    print(f"\nResumo Instituições -> Criadas: {criadas} | Já existentes: {existentes}")


if __name__ == "__main__":
    executar()