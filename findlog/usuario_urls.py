from .usuario_views import usuario_feed
from django.urls import path


urlpatterns = [
    path("", usuario_feed, name="usuario_feed"),


]