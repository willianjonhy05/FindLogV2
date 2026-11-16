from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..serializers.auth import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status


class LoginAPIView(TokenObtainPairView):
    """
    Endpoint para autenticação via App Móvel.
    Recebe POST com { "email": "...", "password": "..." } e retorna { "access": "...", "refresh": "...", "nome": "..." }
    """

    serializer_class = CustomTokenObtainPairSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def perfil_usuario_api_view(request):
    """
    Endpoint protegido para o aplicativo móvel buscar os dados do usuário autenticado no momento.
    """
    user = request.user
    data = {
        "id": user.pk,
        "username": user.username,
        "nome": user.nome,
        "email": user.email,
        "cpf": user.cpf,
        "tipo": user.tipo,
        "ativo": user.ativo,
    }
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_api_view(request):
    """
    Endpoint de logout para o aplicativo móvel.
    Invalida o 'refresh_token' adicionando-o à blacklist do servidor.
    """
    try:
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "O token de atualização (refresh) é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cria a instância do token e o envia para a blacklist
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({"message": "Sessão encerrada com sucesso."}, status=status.HTTP_200_OK)
    except Exception:
        return Response(
            {"error": "Token inválido, expirado ou já utilizado."},
            status=status.HTTP_400_BAD_REQUEST,
        )
