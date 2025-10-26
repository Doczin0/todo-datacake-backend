from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet,
    RegisterView,
    VerifyEmailView,
    ResendCodeView,
    ResolveUsernameView,
    RequestPasswordResetView,
    ConfirmPasswordResetView,
    HealthView,
)
from .auth_tokens import TokenObtainPairView, TokenRefreshView, LogoutView, MeView

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/verify/", VerifyEmailView.as_view(), name="verify-email"),
    path("auth/resend/", ResendCodeView.as_view(), name="resend-code"),
    path("auth/resolve-username/", ResolveUsernameView.as_view(), name="resolve-username"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/password/reset/", RequestPasswordResetView.as_view(), name="password-reset"),
    path("auth/password/confirm/", ConfirmPasswordResetView.as_view(), name="password-confirm"),
    path("health/", HealthView.as_view(), name="health"),
]
