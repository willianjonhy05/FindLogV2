import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")  # Ajuste "setup.settings" se necessário
django.setup()

from findlog.models import Instituicao, Sala


# Modelo padrão de ambientes que serão criados para cada instituição ativa
AMBIENTES_PADRAO = [
    {
        "nome": "Coordenação de Achados e Perdidos",
        "predio": "Bloco A",
        "andar": "Térreo",
        "telefone": "8631311410",
        "descricao": "Guichê central de triagem, guarda e devolução de objetos encontrados.",
        "sala_de_aula": False,
        "laboratorio": False,
        "ativa": True,
    },
    {
        "nome": "Portaria Principal / Recepção",
        "predio": "Bloco A",
        "andar": "Térreo",
        "telefone": "8631311401",
        "descricao": "Guarita e balcão de entrada principal da unidade.",
        "sala_de_aula": False,
        "laboratorio": False,
        "ativa": True,
    },
    {
        "nome": "Sala 101",
        "predio": "Bloco A",
        "andar": "1º Andar",
        "telefone": "",
        "descricao": "Sala de aula teórica próxima à escada central.",
        "sala_de_aula": True,
        "laboratorio": False,
        "ativa": True,
    },
    {
        "nome": "Sala 102",
        "predio": "Bloco A",
        "andar": "1º Andar",
        "telefone": "",
        "descricao": "Sala de aula climatizada com projetor multimídia.",
        "sala_de_aula": True,
        "laboratorio": False,
        "ativa": True,
    },
    {
        "nome": "Laboratório de Informática 01",
        "predio": "Bloco B",
        "andar": "Térreo",
        "telefone": "8631311420",
        "descricao": "Laboratório de desenvolvimento de sistemas e redes.",
        "sala_de_aula": False,
        "laboratorio": True,
        "ativa": True,
    },
    {
        "nome": "Laboratório de Hardware e Manutenção",
        "predio": "Bloco B",
        "andar": "1º Andar",
        "telefone": "8631311422",
        "descricao": "Bancadas técnicas de eletrônica e manutenção de computadores.",
        "sala_de_aula": False,
        "laboratorio": True,
        "ativa": True,
    },
    {
        "nome": "Biblioteca Setorial",
        "predio": "Bloco C",
        "andar": "Térreo",
        "telefone": "8631311430",
        "descricao": "Salão de estudos, guarda-volumes e balcão de empréstimo.",
        "sala_de_aula": False,
        "laboratorio": False,
        "ativa": True,
    },
    {
        "nome": "Auditório Principal",
        "predio": "Bloco C",
        "andar": "1º Andar",
        "telefone": "8631311435",
        "descricao": "Espaço para eventos, palestras e seminários.",
        "sala_de_aula": False,
        "laboratorio": False,
        "ativa": True,
    },
    {
        "nome": "Sala 205 (Em Reforma)",
        "predio": "Bloco B",
        "andar": "2º Andar",
        "telefone": "",
        "descricao": "Ambiente temporariamente interditado para manutenção.",
        "sala_de_aula": True,
        "laboratorio": False,
        "ativa": False,
    },
]


def executar():
    instituicoes = Instituicao.objects.filter(ativo=True)

    if not instituicoes.exists():
        print("[!] Nenhuma instituição ativa encontrada. Execute 'popular_instituicoes.py' primeiro.")
        return

    criadas = 0
    existentes = 0

    for inst in instituicoes:
        print(f"\n--- Populando salas para: {inst.nome} ---")
        for amb in AMBIENTES_PADRAO:
            sala, criada = Sala.objects.get_or_create(
                instituicao=inst,
                nome=amb["nome"],
                predio=amb["predio"],
                defaults={
                    "andar": amb["andar"],
                    "telefone": amb["telefone"],
                    "descricao": amb["descricao"],
                    "sala_de_aula": amb["sala_de_aula"],
                    "laboratorio": amb["laboratorio"],
                    "ativa": amb["ativa"],
                },
            )
            if criada:
                criadas += 1
                print(f"  [+] Criada: {sala.nome} ({sala.predio} - {sala.andar}) | Cód: {sala.codigo}")
            else:
                existentes += 1
                print(f"  [=] Já existia: {sala.nome} ({sala.predio})")

    print(f"\nResumo Salas -> Criadas: {criadas} | Já existentes: {existentes}")


if __name__ == "__main__":
    executar()