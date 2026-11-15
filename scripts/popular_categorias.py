import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")  
django.setup()

from findlog.models import Categoria


CATEGORIAS_DADOS = [
    ("Documentos Pessoais", "RG, CNH, CPF, passaporte, título de eleitor e certidões."),
    ("Cartões Bancários e Transporte", "Cartões de crédito, débito, vale-transporte e passe estudantil."),
    ("Carteiras e Porta-Documentos", "Carteiras de couro, tecido, porta-cartões e pochetes pequenas."),
    ("Smartphones e Celulares", "Aparelhos celulares de todas as marcas e modelos."),
    ("Notebooks e Tablets", "Laptops, iPads, tablets e leitores digitais (Kindle)."),
    ("Fones de Ouvido e Áudio", "Fones com fio, Bluetooth, cases de carregamento e caixas de som."),
    ("Carregadores e Cabos", "Fontes de notebook, carregadores de celular, cabos USB e power banks."),
    ("Pendrives e Mídias", "Pendrives, HDs externos, cartões de memória e adaptadores."),
    ("Chaves e Chaveiros", "Chaves residenciais, chaves de veículos, controles de portão e molhos."),
    ("Óculos de Grau e Sol", "Óculos receituários, óculos escuros e estojos de proteção."),
    ("Relógios e Smartwatches", "Relógios analógicos, digitais e pulseiras inteligentes."),
    ("Joias e Bijuterias", "Anéis, alianças, correntes, brincos, pulseiras e pingentes."),
    ("Mochilas e Bolsas", "Mochilas escolares, bolsas femininas, pastas executivas e sacolas."),
    ("Estojos e Material Escolar", "Estojos, canetas, lapiseiras, calculadoras científicas e réguas."),
    ("Livros e Cadernos", "Livros didáticos, obras literárias, cadernos, agendas e apostilas."),
    ("Garrafas e Copos Térmicos", "Squeezes, garrafas de água, copos térmicos e marmitas."),
    ("Vestuário e Agasalhos", "Casacos, jaquetas, camisas, jalecos e uniformes."),
    ("Bonés, Chapéus e Acessórios", "Bonés, toucas, cintos, lenços e gravatas."),
    ("Guarda-Chuvas e Sombrinhas", "Guarda-chuvas dobráveis, sombrinhas e capas de chuva."),
    ("Equipamentos de Laboratório", "Jalecos técnicos, óculos de proteção, multímetros e componentes."),
    ("Instrumentos Musicais", "Violões, flautas, baquetas, afinadores e capas de instrumentos."),
    ("Artigos Esportivos", "Bolas, raquetes, garrafas esportivas, luvas e tênis."),
    ("Brinquedos e Itens Infantis", "Brinquedos, mamadeiras, chupetas e acessórios infantis."),
    ("Medicamentos e Saúde", "Caixas de remédios, inaladores, aparelhos de pressão e receitas."),
    ("Outros Objetos", "Itens diversos que não se enquadram nas categorias anteriores."),
]


def executar():
    criadas = 0
    existentes = 0

    for nome, descricao in CATEGORIAS_DADOS:
        categoria, criada = Categoria.objects.get_or_create(
            nome=nome,
            defaults={
                "descricao": descricao,
                "ativa": True,
            },
        )
        if criada:
            criadas += 1
            print(f"[+] Categoria criada: {categoria.nome} (slug: {categoria.slug})")
        else:
            existentes += 1
            print(f"[=] Já existia: {categoria.nome}")

    print(f"\nResumo Categorias -> Criadas: {criadas} | Já existentes: {existentes}")


if __name__ == "__main__":
    executar()