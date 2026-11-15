import os
import sys
from datetime import timedelta
import django
from django.utils import timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")  # Ajuste "setup.settings" se necessário
django.setup()

from findlog.models import Instituicao, Categoria, Sala, Perfil, Item


ITENS_DADOS = [
    ("Garrafa Térmica Azul 750ml", "Garrafas e Copos Térmicos", "Garrafa de inox azul fosco com tampa preta e alguns adesivos na lateral."),
    ("Carteira de Couro Marrom", "Carteiras e Porta-Documentos", "Carteira masculina contendo cartões bancários e documento estudantil."),
    ("Fone de Ouvido Bluetooth Branco", "Fones de Ouvido e Áudio", "Estojo carregador branco com ambos os fones dentro, sem marca aparente."),
    ("Carregador de Notebook Lenovo 65W", "Carregadores e Cabos", "Fonte original preta com cabo de força padrão brasileiro."),
    ("Molho de Chaves com Chaveiro de Metal", "Chaves e Chaveiros", "Três chaves simples e um chaveiro metálico prateado formato torre."),
    ("Óculos de Grau Armação Preta", "Óculos de Grau e Sol", "Óculos de grau com armação quadrada em acetato preto dentro de estojo cinza."),
    ("Calculadora Científica Casio fx-82MS", "Estojos e Material Escolar", "Calculadora cinza com tampa protetora deslizante e etiqueta raspada atrás."),
    ("Mochila Preta Notebook 15.6", "Mochilas e Bolsas", "Mochila de nylon preta com dois compartimentos e bolso lateral telado."),
    ("Guarda-Chuva Dobrável Azul Marinho", "Guarda-Chuvas e Sombrinhas", "Guarda-chuva compacto automático com capa protetora azul marinho."),
    ("Relógio Digital Preto Esportivo", "Relógios e Smartwatches", "Relógio de pulseira de silicone preta encontrado próximo à quadra/pátio."),
    ("Jaleco Branco Manga Longa Tam. M", "Vestuário e Agasalhos", "Jaleco em tecido gabardine branco com dois bolsos frontais, sem bordado."),
    ("Livro - Engenharia de Software (Sommerville)", "Livros e Cadernos", "Livro capa brochura em bom estado com marca-páginas amarelo."),
    ("Pendrive SanDisk 32GB Preto e Vermelho", "Pendrives e Mídias", "Pendrive retrátil sem tampa encontrado conectado em um dos computadores."),
    ("Smartphone Motorola Moto G Azul", "Smartphones e Celulares", "Aparelho com capa transparente amarelada e película trincada no canto."),
    ("Caderno Universitário 10 Matérias", "Livros e Cadernos", "Caderno espiral capa preta com anotações de algoritmos e matemática discreta."),
    ("Estojo Escolar Verde Água", "Estojos e Material Escolar", "Estojo de zíper contendo canetas coloridas, lapiseira 0.7 e borracha branca."),
    ("Cartão de Passe Estudantil", "Cartões Bancários e Transporte", "Cartão de transporte público encontrado próximo à catraca de entrada."),
    ("Boné Preto Aba Curva", "Bonés, Chapéus e Acessórios", "Boné básico de sarja preta com fecho ajustável traseiro."),
    ("Power Bank 10000mAh Cinza", "Carregadores e Cabos", "Carregador portátil metálico cinza escuro com cabo USB-C curto."),
    ("Casaco Moletom Cinza Mescla", "Vestuário e Agasalhos", "Blusa de moletom com capuz e bolso canguru, tamanho G."),
    ("Óculos de Sol Aviador Dourado", "Óculos de Grau e Sol", "Óculos estilo aviador com lentes escuras esverdeadas, sem estojo."),
    ("RG e CPF em Plástico Protetor", "Documentos Pessoais", "Documentos pessoais encontrados no corredor principal."),
    ("Smartwatch Pulseira Rosa Claro", "Relógios e Smartwatches", "Relógio inteligente descarregado encontrado no sanitário feminino."),
    ("Squeeze Transparente 1 Litro", "Garrafas e Copos Térmicos", "Garrafa plástica transparente com medidor de horário na lateral."),
    ("Mouse Sem Fio Logitech Preto", "Pendrives e Mídias", "Mouse óptico sem fio com receptor USB guardado dentro do compartimento da pilha."),
]


def executar():
    instituicoes = list(Instituicao.objects.filter(ativo=True).order_by("nome"))
    if not instituicoes:
        print("[!] Nenhuma instituição ativa encontrada. Execute 'popular_instituicoes.py' primeiro.")
        return

    categorias_map = {c.nome: c for c in Categoria.objects.filter(ativa=True)}
    categoria_fallback = Categoria.objects.filter(ativa=True).first()
    if not categoria_fallback:
        print("[!] Nenhuma categoria ativa encontrada. Execute 'popular_categorias.py' primeiro.")
        return

    criados = 0
    existentes = 0
    agora = timezone.now()

    for idx, (nome, nome_categoria, descricao) in enumerate(ITENS_DADOS):
        inst = instituicoes[idx % len(instituicoes)]
        categoria = categorias_map.get(nome_categoria, categoria_fallback)

        # Busca salas da instituição (local onde foi encontrado e sala de guarda)
        salas_inst = list(Sala.objects.filter(instituicao=inst, ativa=True))
        sala_encontrado = salas_inst[(idx + 2) % len(salas_inst)] if salas_inst else None
        sala_guarda = (
            Sala.objects.filter(instituicao=inst, nome__icontains="Achados").first()
            or (salas_inst[0] if salas_inst else None)
        )

        # Busca um servidor ativo vinculado a essa instituição para registrar o item
        servidor_registro = (
            Perfil.objects.filter(
                tipo=Perfil.TipoUsuario.SERVIDOR,
                ativo=True,
                instituicao=inst,
            ).first()
            or Perfil.objects.filter(is_superuser=True).first()
        )

        item, criado = Item.objects.get_or_create(
            nome=nome,
            instituicao=inst,
            defaults={
                "descricao": descricao,
                "categoria": categoria,
                "local": sala_encontrado,
                "local_guardado": sala_guarda,
                "usuario_registro": servidor_registro,
                "status": Item.StatusItem.ENCONTRADO,
            },
        )

        if criado:
            data_retroativa = agora - timedelta(days=idx, hours=(idx % 8) + 1)
            Item.objects.filter(pk=item.pk).update(data_registro=data_retroativa)
            criados += 1
            print(f"[+] Item criado: {item.nome} | Cód: {item.codigo} | Unidade: {inst.nome}")
        else:
            existentes += 1
            print(f"[=] Já existia: {item.nome} ({inst.nome})")

    print(f"\nResumo Itens -> Criados: {criados} | Já existentes: {existentes}")


if __name__ == "__main__":
    executar()