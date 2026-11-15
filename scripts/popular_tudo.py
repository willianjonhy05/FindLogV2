import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")  # Ajuste "setup.settings" se necessário
django.setup()

from scripts import (
    popular_instituicoes,
    popular_salas,
    popular_categorias,
    popular_contatos,
)


if __name__ == "__main__":
    print("=== INICIANDO POPULAÇÃO DE DADOS DO FINDLOG ===\n")
    popular_instituicoes.executar()
    print("\n" + "-" * 50 + "\n")
    popular_salas.executar()
    print("\n" + "-" * 50 + "\n")
    popular_categorias.executar()
    print("\n" + "-" * 50 + "\n")
    popular_contatos.executar()
    print("\n=== CONCLUÍDO COM SUCESSO ===")