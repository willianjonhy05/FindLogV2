from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from ..views.auth_views import LoginAPIView, perfil_usuario_api_view, logout_api_view

urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='api_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('auth/logout/', logout_api_view, name='api_logout'),
    path('auth/me/', perfil_usuario_api_view, name='api_usuario_me'),
]