import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .view_utils import ERRO_INTERNO, extrair_periodo
from ..services.horas_svc import get_horas_por_funcionario, get_nomes_funcionarios_projeto

logger = logging.getLogger(__name__)


@require_GET
def get_horas_por_funcionario_view(request, projeto_id):
    try:
        data_inicio, data_fim = extrair_periodo(request)
        funcionario = request.GET.get('funcionario') or None
        dados = get_horas_por_funcionario(
            projeto_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            funcionario=funcionario,
        )
        return JsonResponse(dados, safe=False)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.exception('Erro interno na view de horas')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)


@require_GET
def get_nomes_funcionarios_view(request, projeto_id):
    try:
        return JsonResponse(get_nomes_funcionarios_projeto(projeto_id), safe=False)
    except Exception as e:
        logger.exception('Erro interno na view de horas')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)
