import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .view_utils import ERRO_INTERNO
from ..services.alertas_svc import get_alertas_materiais, get_estoque_tabela
from ..services.compras_svc import listar_materiais_com_compras, get_lead_time_por_material
from ..services.alertas_svc import get_alertas_materiais
from ..services.compras_svc import listar_materiais_com_compras, get_lead_time_por_material, get_sugestao_proxima_compra

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


@require_GET
def get_estoque_tabela_view(request):
    try:
        critico_max_raw = request.GET.get('critico_max', '30')
        atencao_max_raw = request.GET.get('atencao_max', '60')
        page_raw = request.GET.get('page', '1')
        material_id_raw = request.GET.get('material_id')
        sort_by = request.GET.get('sort_by', 'status')
        sort_dir = request.GET.get('sort_dir', 'asc')
        try:
            critico_max = max(1, int(critico_max_raw))
            atencao_max = max(critico_max + 1, int(atencao_max_raw))
            page = max(1, int(page_raw))
            material_id = int(material_id_raw) if material_id_raw else None
        except ValueError:
            return JsonResponse({'error': 'Parâmetros inválidos'}, status=400)
        data = get_estoque_tabela(critico_max=critico_max, atencao_max=atencao_max, page=page, material_id=material_id, sort_by=sort_by, sort_dir=sort_dir)
        return JsonResponse(data)
    except Exception:
        logger.exception('Erro ao buscar tabela de estoque')
    
@require_GET
def get_sugestao_proxima_compra_view(request):
    try:
        data_referencia_raw = request.GET.get('data_referencia')

        data_referencia = None
        if data_referencia_raw:
            try:
                data_referencia = datetime.strptime(data_referencia_raw, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse(
                    {'error': 'data_referencia deve estar no formato YYYY-MM-DD'},
                    status=400,
                )

        data = get_sugestao_proxima_compra(data_referencia=data_referencia)
        return JsonResponse(data)

    except Exception:
        logger.exception('Erro ao buscar sugestão de próxima compra')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)
