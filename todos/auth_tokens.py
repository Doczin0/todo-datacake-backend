from __future__ import annotations

import logging

from django.contrib.auth import authenticate, get_user_model
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

log = logging.getLogger("todos")
User = get_user_model()


def _find_username(identifier: str) -> str | None:
    """Resolve identifier to a username (supports username or e-mail)."""
    value = (identifier or "").strip()
    if not value:
        return None

    if "@" in value:
        try:
            return User.objects.get(email__iexact=value).username
        except User.DoesNotExist:
            return None

    try:
        return User.objects.get(username__iexact=value).username
    except User.DoesNotExist:
        return None


def _user_payload(user: User) -> dict:
    return {"id": user.id, "username": user.username, "email": user.email}


class TokenObtainPairView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = (
            request.data.get("identifier")
            or request.data.get("username")
            or ""
        ).strip()
        password = (request.data.get("password") or "").strip()

        if not identifier or not password:
            return Response({"detail": "Informe usuario/email e senha."}, status=400)

        username = _find_username(identifier)
        if not username:
            return Response({"detail": "Usuario ou email nao encontrado."}, status=400)

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail": "Credenciais invalidas."}, status=400)

        if not user.is_active:
            return Response({"detail": "Conta ainda nao verificada."}, status=400)

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        log.info("Login OK username=%s", username)
        return Response(
            {
                "detail": "Autenticado com sucesso.",
                "access": access,
                "refresh": str(refresh),
                "user": _user_payload(user),
            },
            status=200,
        )


class TokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = (request.data.get("refresh") or "").strip()
        if not token:
            return Response({"detail": "Refresh token ausente."}, status=400)

        try:
            refresh = RefreshToken(token)
        except TokenError:
            return Response({"detail": "Refresh token invalido ou expirado."}, status=401)

        return Response(
            {
                "detail": "Token atualizado.",
                "access": str(refresh.access_token),
            },
            status=200,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # JWT stateless logout: client simply discards the stored tokens
        return Response({"detail": "Logout efetuado. Tokens revogados apenas no cliente."}, status=200)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(_user_payload(request.user), status=200)
