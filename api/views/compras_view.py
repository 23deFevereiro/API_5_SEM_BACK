import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view

from ..services.alertas_svc import get_alertas_materiais
from ..services.compras_svc import get_lead_time_por_material, listar_materiais_com_compras
from .view_utils import ERRO_INTERNO, resposta_erro, resposta_sucesso, schema_array, schema_obj, schema_paginada

logger = logging.getLogger(__name__)

MATERIAL_COMPRA_SCHEMA = schema_obj({
    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
    'codigo_material': openapi.Schema(type=openapi.TYPE_STRING),
    'descricao': openapi.Schema(type=openapi.TYPE_STRING),
})

LEAD_TIME_ITEM_SCHEMA = schema_obj({
    'fornecedor': openapi.Schema(type=openapi.TYPE_STRING),
    'lead_time': openapi.Schema(type=openapi.TYPE_NUMBER),
    'valor_unidade': openapi.Schema(type=openapi.TYPE_NUMBER),
    'valor_total': openapi.Schema(type=openapi.TYPE_NUMBER),
    'status': openapi.Schema(type=openapi.TYPE_STRING),
    'categoria_status': openapi.Schema(type=openapi.TYPE_STRING),
    'data_pedido': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
})

ALERTA_ITEM_SCHEMA = schema_obj({
    'material': openapi.Schema(type=openapi.TYPE_STRING),
    'dias_para_pedir': openapi.Schema(type=openapi.TYPE_INTEGER),
    'lead_time_min': openapi.Schema(type=openapi.TYPE_INTEGER),
    'fornecedor': openapi.Schema(type=openapi.TYPE_STRING),
    'dias_cobertura': openapi.Schema(type=openapi.TYPE_INTEGER),
})

ALERTAS_RESPONSE_SCHEMA = schema_obj({
    'criticos': schema_array(ALERTA_ITEM_SCHEMA),
    'atencao': schema_array(ALERTA_ITEM_SCHEMA),
})

ESTOQUE_ITEM_SCHEMA = schema_obj({
    'material': openapi.Schema(type=openapi.TYPE_STRING),
    'projeto': openapi.Schema(type=openapi.TYPE_STRING),
    'estoque_atual': openapi.Schema(type=openapi.TYPE_INTEGER),
    'consumo_previsto': openapi.Schema(type=openapi.TYPE_NUMBER),
    'dias_ate_acabar': openapi.Schema(type=openapi.TYPE_INTEGER),
    'status': openapi.Schema(type=openapi.TYPE_STRING),
})


@swagger_auto_schema(
    method='get',
    operation_summary='Lista materiais de compras',
    operation_description='Retorna os materiais com informacoes consolidadas para acompanhamento do processo de compras.',
    responses={
        200: resposta_sucesso('Lista de materiais encontrados no modulo de compras.', schema_array(MATERIAL_COMPRA_SCHEMA)),
        500: resposta_erro('Erro interno ao listar materiais de compras.'),
    },
)
@api_view(['GET'])
@require_GET
def listar_materiais_compras_view(request):
    try:
        materiais = listar_materiais_com_compras()
        return JsonResponse(materiais, safe=False)
    except Exception:
        logger.exception('Erro ao listar materiais de compras')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)


@swagger_auto_schema(
    method='get',
    operation_summary='Consulta lead time por material',
    operation_description='Retorna os dados de lead time de um material especifico a partir do parametro de consulta material_id.',
    responses={
        200: resposta_sucesso('Historico de lead time do material informado.', schema_array(LEAD_TIME_ITEM_SCHEMA)),
        400: resposta_erro('Parametro material_id ausente ou invalido.'),
        500: resposta_erro('Erro interno ao buscar dados de lead time.'),
    },
)
@api_view(['GET'])
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


@swagger_auto_schema(
    method='get',
    operation_summary='Lista alertas de materiais',
    operation_description='Retorna os alertas de materiais classificados por criticidade com base nos limites informados nos parametros critico_max e atencao_max.',
    responses={
        200: resposta_sucesso('Alertas agrupados por criticidade.', ALERTAS_RESPONSE_SCHEMA),
        400: resposta_erro('Parametros critico_max ou atencao_max invalidos.'),
        500: resposta_erro('Erro interno ao buscar alertas de materiais.'),
    },
)
@api_view(['GET'])
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


@swagger_auto_schema(
    method='get',
    operation_summary='Consulta tabela de estoque',
    operation_description='Retorna a tabela paginada de estoque com filtros por material e opcoes de ordenacao e classificacao de criticidade.',
    responses={
        200: resposta_sucesso('Tabela paginada de estoque dos materiais.', schema_paginada(ESTOQUE_ITEM_SCHEMA)),
        400: resposta_erro('Um ou mais parametros de consulta sao invalidos.'),
        500: resposta_erro('Erro interno ao buscar a tabela de estoque.'),
    },
)
@api_view(['GET'])
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
        return JsonResponse({'error': ERRO_INTERNO}, status=500)
    
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

