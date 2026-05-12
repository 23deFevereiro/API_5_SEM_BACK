import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .view_utils import ERRO_INTERNO
from ..services.alertas_svc import get_alertas_materiais
from ..services.compras_svc import listar_materiais_com_compras, get_lead_time_por_material

logger = logging.getLogger(__name__)


@require_GET
def listar_materiais_compras_view(request):
    try:
        materiais = listar_materiais_com_compras()
        return JsonResponse(materiais, safe=False)
    except Exception:
        logger.exception('Erro ao listar materiais de compras')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)


@require_GET
def get_lead_time_view(request):
    material_id_raw = request.GET.get('material_id')
    if not material_id_raw:
        return JsonResponse({'error': 'material_id é obrigatório'}, status=400)
    try:
        material_id = int(material_id_raw)
    except ValueError:
        return JsonResponse({'error': 'material_id inválido'}, status=400)
    try:
        data = get_lead_time_por_material(material_id)
        return JsonResponse(data, safe=False)
    except Exception:
        logger.exception('Erro ao buscar dados de lead time')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)


@require_GET
def get_alertas_view(request):
    try:
        critico_max_raw = request.GET.get('critico_max', '30')
        atencao_max_raw = request.GET.get('atencao_max', '60')
        try:
            critico_max = max(1, int(critico_max_raw))
            atencao_max = max(critico_max + 1, int(atencao_max_raw))
        except ValueError:
            return JsonResponse({'error': 'critico_max e atencao_max devem ser inteiros'}, status=400)
        data = get_alertas_materiais(critico_max=critico_max, atencao_max=atencao_max)
        return JsonResponse(data)
    except Exception:
        logger.exception('Erro ao buscar alertas de materiais')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)
