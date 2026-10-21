from django.shortcuts import render



def servidor_painel(request):
    return render(request, "servidor/index.html")