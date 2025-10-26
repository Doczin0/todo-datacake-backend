# todos/exceptions.py
import logging
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Envolve o handler padrão do DRF para:
    - logar erros de forma consistente
    - devolver mensagens mais legíveis ao frontend
    """
    response = drf_exception_handler(exc, context)

    view = context.get("view")
    view_name = getattr(view, "__class__", type("V", (), {})).__name__
    req = context.get("request")

    if response is not None:
        # Erros tratados pelo DRF (ValidationError, NotAuthenticated, etc.)
        logger.warning(
            "Handled error [%s] %s %s -> %s %s",
            view_name,
            req.method if req else "-",
            req.get_full_path() if req else "-",
            response.status_code,
            getattr(exc, "detail", repr(exc)),
        )

        # Normalize a estrutura da resposta para ficar consistente
        data = response.data
        if isinstance(data, dict):
            # mantém chaves de campo quando houver; adiciona 'detail' amigável
            if "detail" not in data:
                data["detail"] = "Houve um problema com sua requisição."
            return Response(data, status=response.status_code)
        else:
            return Response({"detail": str(data)}, status=response.status_code)

    # Erros não tratados → 500
    logger.exception(
        "Unhandled error [%s] %s %s",
        view_name,
        req.method if req else "-",
        req.get_full_path() if req else "-",
        exc_info=exc,
    )
    return Response(
        {"detail": "Erro interno inesperado. Tente novamente mais tarde."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
