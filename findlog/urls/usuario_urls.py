from django.urls import path
from ..views.usuario_views import minhas_reivindicacoes, usuario_feed_por_categoria, usuario_feed, detalhar_item

urlpatterns = [
    path("", usuario_feed, name="usuario_feed"),
    path("item/<uuid:uuid>/", detalhar_item, name="usuario_detalhar_item"),
    path("minhas-reivindicacoes/", minhas_reivindicacoes, name="minhas_reivindicacoes"),
    path("categoria/<slug:slug>/", usuario_feed_por_categoria, name="usuario_feed_por_categoria"),


]