import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from ..services.funcionario_svc import get_funcionarios_projeto
from .view_utils import ERRO_INTERNO, extrair_periodo

logger = logging.getLogger(__name__)


@require_GET
def get_funcionarios_projeto_view(request, projeto_id):
    try:
        page = request.GET.get("page", 1)
        data_inicio, data_fim = extrair_periodo(request)
        funcionario = request.GET.get("funcionario") or None
        funcionarios = get_funcionarios_projeto(
            projeto_id,
            page=page,
            page_size=10,
            data_inicio=data_inicio,
            data_fim=data_fim,
            funcionario=funcionario,
        )
        return JsonResponse(funcionarios)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception:
        logger.exception("Erro interno na view de funcionário")
        return JsonResponse({"error": ERRO_INTERNO}, status=500)
