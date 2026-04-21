import logging

from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET

from .view_utils import ERRO_INTERNO, extrair_periodo

logger = logging.getLogger(__name__)
from ..services.projeto_svc import (
    listar_projetos,
    get_resumo_projeto,
    get_materiais_projeto,
    get_overview_data_all,
    get_materiais_disponiveis,
)


def _extrair_programa_id(request):
    """Retorna programa_id como int ou None se ausente/inválido."""
    raw = request.GET.get('programa_id')
    try:
        return int(raw) if raw else None
    except ValueError:
        return None


@require_GET
def get_overview_projetos(request):
    programa_id = _extrair_programa_id(request)
    overview = get_overview_data_all(programa_id=programa_id)
    return JsonResponse(overview, safe=False)

@require_GET
def listar_projetos_view(request):
    search = request.GET.get('search', '')
    programa_id = _extrair_programa_id(request)
    projetos = listar_projetos(search, programa_id=programa_id)
    return JsonResponse(projetos, safe=False)

@require_GET
def get_resumo_projeto_view(request, projeto_id):
    try:
        resumo = get_resumo_projeto(projeto_id)
        return JsonResponse(resumo)
    except Http404:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)
    except Exception as e:
        logger.exception('Erro interno na view de projeto')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)

@require_GET
def get_materiais_projeto_view(request, projeto_id):
    try:
        page = request.GET.get('page', 1)
        data_inicio, data_fim = extrair_periodo(request)
        material = request.GET.get('material') or None
        materiais = get_materiais_projeto(
            projeto_id,
            page=page,
            page_size=10,
            data_inicio=data_inicio,
            data_fim=data_fim,
            material=material,
        )
        return JsonResponse(materiais)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Http404:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)
    except Exception as e:
        logger.exception('Erro interno na view de projeto')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)


@require_GET
def get_materiais_disponiveis_view(request, projeto_id):
    try:
        return JsonResponse(get_materiais_disponiveis(projeto_id), safe=False)
    except Exception as e:
        logger.exception('Erro interno na view de projeto')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)