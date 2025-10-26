from __future__ import annotations

import re

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import timedelta

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmailVerificationCode, Task
from .serializers import RegisterSerializer, TaskSerializer

User = get_user_model()


# -------- TASKS --------
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = (
            Task.objects.filter(owner=self.request.user)
            .prefetch_related("checklist_items")
            .order_by("-created_at")
        )
        status_param = self.request.query_params.get("status")
        if status_param in ("pendente", "concluida"):
            queryset = queryset.filter(status=status_param)

        importance_param = self.request.query_params.get("importance")
        if importance_param in ("baixa", "media", "alta"):
            queryset = queryset.filter(importance=importance_param)

        category_param = self.request.query_params.get("category")
        if category_param:
            queryset = queryset.filter(category=category_param)

        tag_param = self.request.query_params.get("tag")
        if tag_param:
            queryset = queryset.filter(tags__contains=[tag_param])

        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(created_at__date__gte=parse_date(date_from))

        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(created_at__date__lte=parse_date(date_to))

        due_from = self.request.query_params.get("due_from")
        if due_from:
            queryset = queryset.filter(due_date__gte=parse_date(due_from))

        due_to = self.request.query_params.get("due_to")
        if due_to:
            queryset = queryset.filter(due_date__lte=parse_date(due_to))

        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        task = self.get_object()
        new_status = "concluida" if task.status == "pendente" else "pendente"
        task.status = new_status

        update_fields = ["status"]
        if task.recurrence != "nenhuma":
            task.recurrence = "nenhuma"
            update_fields.append("recurrence")

        task.save(update_fields=update_fields)

        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


def _normalize_email(value: str | None) -> str:
    return (value or "").strip().lower()


def _pull_latest_code(user: User) -> EmailVerificationCode | None:
    return EmailVerificationCode.objects.filter(user=user).first()


# -------- AUTH: REGISTER / VERIFY / RESEND --------
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        code = EmailVerificationCode.generate_code()
        EmailVerificationCode.objects.create(user=user, code=code)
        send_mail(
            "Código de verificação - DataCake",
            f"Seu código é {code} (expira em 2 minutos).",
            "no-reply@datacake.local",
            [user.email],
        )
        return Response(
            {"detail": "Usuário criado. Código exibido no console."},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = _normalize_email(request.data.get("email"))
        code = (request.data.get("code") or request.data.get("token") or "").strip()
        if not email or not code:
            return Response(
                {"error": "E-mail e código são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"error": "E-mail ou código inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification = _pull_latest_code(user)
        if not verification:
            return Response(
                {"error": "Código não encontrado ou expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not verification.is_valid():
            verification.delete()
            return Response(
                {"error": "Código expirado."}, status=status.HTTP_400_BAD_REQUEST
            )
        if verification.code != code:
            return Response(
                {"error": "Código ou token incorreto."}, status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = True
        user.save(update_fields=["is_active"])
        EmailVerificationCode.objects.filter(user=user).delete()
        return Response(
            {"detail": "Conta verificada! Faça login para continuar.", "redirect": "login"},
            status=status.HTTP_200_OK,
        )


class ResendCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = _normalize_email(request.data.get("email"))
        if not email:
            return Response(
                {"error": "E-mail é obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"error": "E-mail não encontrado."}, status=status.HTTP_400_BAD_REQUEST
            )

        verification = _pull_latest_code(user)
        if not verification:
            return Response(
                {"error": "Código não encontrado. Solicite um novo cadastro."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verification.resend_count >= 2:
            return Response(
                {"error": "Limite de reenvios atingido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification.code = EmailVerificationCode.generate_code()
        verification.created_at = timezone.now()
        verification.resend_count += 1
        verification.save(update_fields=["code", "created_at", "resend_count"])

        send_mail(
            "Novo código - DataCake",
            f"Seu novo código é {verification.code} (expira em 2 minutos).",
            "no-reply@datacake.local",
            [user.email],
        )
        return Response(
            {"detail": "Novo código exibido no console."},
            status=status.HTTP_200_OK,
        )


# -------- LOGIN (resolve e-mail para username, se necessário) --------
class ResolveUsernameView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = (request.data.get("identifier") or "").strip()
        if not identifier:
            return Response(
                {"detail": "Informe usuário ou e-mail."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "@" in identifier:
            try:
                user = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                return Response(
                    {"detail": "E-mail não encontrado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response({"username": user.username}, status=status.HTTP_200_OK)

        try:
            User.objects.get(username__iexact=identifier)
        except User.DoesNotExist:
            return Response(
                {"detail": "Usuário não encontrado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"username": identifier}, status=status.HTTP_200_OK)


# -------- PASSWORD RESET --------
class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = _normalize_email(request.data.get("email"))
        if not email:
            return Response(
                {"error": "E-mail obrigatório."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"error": "E-mail não cadastrado."}, status=status.HTTP_400_BAD_REQUEST
            )

        code = EmailVerificationCode.generate_code()
        EmailVerificationCode.objects.create(user=user, code=code)
        send_mail(
            "Redefinição de Senha - DataCake",
            f"Seu código para redefinir senha é {code} (expira em 2 minutos).",
            "no-reply@datacake.local",
            [user.email],
        )
        return Response(
            {"detail": "Código de redefinição exibido no console."},
            status=status.HTTP_200_OK,
        )


class ConfirmPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = _normalize_email(request.data.get("email"))
        code = (request.data.get("code") or request.data.get("token") or "").strip()
        password = (request.data.get("password") or "").strip()

        if not all([email, code, password]):
            return Response(
                {"error": "Todos os campos são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Código ou e-mail inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification = _pull_latest_code(user)
        if not verification or not verification.is_valid():
            if verification:
                verification.delete()
            return Response(
                {"error": "Código expirado ou inexistente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verification.code != code:
            return Response(
                {"error": "Código ou token incorreto."}, status=status.HTTP_400_BAD_REQUEST
            )

        password_policy_msg = (
            "A senha deve ter 8+ caracteres, com maiúscula, minúscula, número e símbolo."
        )
        if len(password) < 8:
            return Response(
                {"error": password_policy_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not re.search(r"[A-Z]", password):
            return Response(
                {"error": password_policy_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not re.search(r"[a-z]", password):
            return Response(
                {"error": password_policy_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not re.search(r"[0-9]", password):
            return Response(
                {"error": password_policy_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not re.search(r"[^A-Za-z0-9]", password):
            return Response(
                {"error": password_policy_msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.check_password(password):
            return Response(
                {"error": "A nova senha não pode ser igual à anterior."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save(update_fields=["password"])
        EmailVerificationCode.objects.filter(user=user).delete()
        return Response(
            {"detail": "Senha redefinida com sucesso!"},
            status=status.HTTP_200_OK,
        )


class HealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
