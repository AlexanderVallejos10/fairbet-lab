from django.shortcuts import get_object_or_404
from drf_spectacular.openapi import AutoSchema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserProfile
from .serializers import RegisterSerializer, UserProfileSerializer


class RegisterView(APIView):
    schema = AutoSchema()
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = serializer.save()

        return Response(
            {
                "message": "Usuario registrado correctamente.",
                "profile": UserProfileSerializer(profile).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MyProfileView(APIView):
    schema = AutoSchema()
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        return Response(UserProfileSerializer(profile).data)