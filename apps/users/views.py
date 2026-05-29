from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PerfilUsuario
from .serializers import PerfilUsuarioSerializer, RegistroSerializer


class RegistroView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        perfil = serializer.save()
        return Response(
            {
                "message": "Usuario registrado correctamente.",
                "perfil": PerfilUsuarioSerializer(perfil).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PerfilActualView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        perfil = getattr(request.user, "perfil", None)
        if not perfil:
            return Response(
                {"message": "El usuario no tiene perfil."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PerfilUsuarioSerializer(perfil).data)