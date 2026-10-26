from django.shortcuts import render



def servidor_painel(request):
    return render(request, "servidor/index.html")


def cadastrar_sala(request):
    pass


def listar_itens_por_sala(request):
    pass