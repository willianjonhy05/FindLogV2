from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from findlog.models import Perfil

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customiza o token JWT para aceitar autenticação e injetar dados extras do usuário (Perfil) na resposta.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Adiciona claims personalizados ao payload do token se necessário
        token['username'] = user.username
        token['email'] = user.email
        token['tipo'] = user.tipo
        return token

    def validate(self, attrs):
        # O SimpleJWT usa 'username' por padrão. Se o seu projeto usa email, ajustamos aqui:
        email = attrs.get("email") or attrs.get("username")
        password = attrs.get("password")

        # Valida se o usuário existe e está ativo antes de emitir o token
        try:
            user = Perfil.objects.get(email=email)
            if not user.is_active or not user.ativo:
                raise serializers.ValidationError("Esta conta de acesso está desativada.")
        except Perfil.DoesNotExist:
            pass

        data = super().validate(attrs)
        
        # Adiciona dados úteis do perfil na resposta JSON do login para o App consumir direto
        data['nome'] = self.user.nome
        data['email'] = self.user.email
        data['tipo'] = self.user.tipo
        data['username'] = self.user.username
        
        return data