import logging

from drf_yasg import openapi
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema

from .view_utils import ERRO_INTERNO, ERRO_INTERNO_VIEW_PROJETO, extrair_periodo, resposta_erro, resposta_sucesso, schema_array, schema_obj, schema_paginada

logger = logging.getLogger(__name__)
from ..services.projeto_svc import (
    listar_projetos,
    get_resumo_projeto,
    get_materiais_projeto,
    get_overview_data_all,
    get_materiais_disponiveis,
)

OVERVIEW_VALUE_SCHEMA = schema_obj({
    'codigo_projeto': openapi.Schema(type=openapi.TYPE_STRING),
    'nome_projeto': openapi.Schema(type=openapi.TYPE_STRING),
    'cost': openapi.Schema(type=openapi.TYPE_NUMBER),
})

OVERVIEW_GRUPO_SCHEMA = schema_obj({
    'date_str': openapi.Schema(type=openapi.TYPE_STRING),
    'values': schema_array(OVERVIEW_VALUE_SCHEMA),
})

PROJETO_SCHEMA = schema_obj({
    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
    'codigo_projeto': openapi.Schema(type=openapi.TYPE_STRING),
    'nome_projeto': openapi.Schema(type=openapi.TYPE_STRING),
})

RESUMO_PROJETO_SCHEMA = schema_obj({
    'custo_total': openapi.Schema(type=openapi.TYPE_NUMBER),
    'tempo_total': openapi.Schema(type=openapi.TYPE_NUMBER),
})

MATERIAL_PROJETO_SCHEMA = schema_obj({
    'nome_material': openapi.Schema(type=openapi.TYPE_STRING),
    'quantidade': openapi.Schema(type=openapi.TYPE_NUMBER),
    'custo_total_estimado': openapi.Schema(type=openapi.TYPE_NUMBER),
})

MATERIAL_DISPONIVEL_SCHEMA = schema_obj({
    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
    'descricao': openapi.Schema(type=openapi.TYPE_STRING),
})


def _extrair_programa_id(request):
    """Retorna programa_id como int ou None se ausente/inválido."""
    raw = request.GET.get('programa_id')
    try:
        return int(raw) if raw else None
    except ValueError:
        return None


@swagger_auto_schema(
    method='get',
    operation_summary='Consulta visao geral dos projetos',
    operation_description='Retorna uma visao geral dos projetos, com filtro opcional pelo parametro programa_id.',
    responses={
        200: resposta_sucesso('Visao geral dos custos acumulados por projeto ao longo do tempo.', schema_array(OVERVIEW_GRUPO_SCHEMA)),
    },
)
@api_view(['GET'])
@require_GET
def get_overview_projetos(request):
    programa_id = _extrair_programa_id(request)
    overview = get_overview_data_all(programa_id=programa_id)
    return JsonResponse(overview, safe=False)

@swagger_auto_schema(
    method='get',
    operation_summary='Lista projetos',
    operation_description='Retorna os projetos cadastrados com filtro textual opcional e filtro por programa.',
    responses={
        200: resposta_sucesso('Lista de projetos cadastrados.', schema_array(PROJETO_SCHEMA)),
    },
)
@api_view(['GET'])
@require_GET
def listar_projetos_view(request):
    search = request.GET.get('search', '')
    programa_id = _extrair_programa_id(request)
    projetos = listar_projetos(search, programa_id=programa_id)
    return JsonResponse(projetos, safe=False)

@swagger_auto_schema(
    method='get',
    operation_summary='Consulta resumo do projeto',
    operation_description='Retorna o resumo consolidado do projeto informado pelo identificador na URL.',
    responses={
        200: resposta_sucesso('Resumo consolidado do projeto.', RESUMO_PROJETO_SCHEMA),
        404: resposta_erro('Projeto nao encontrado.'),
        500: resposta_erro('Erro interno ao buscar resumo do projeto.'),
    },
)
@api_view(['GET'])
@require_GET
def get_resumo_projeto_view(request, projeto_id):
    try:
        resumo = get_resumo_projeto(projeto_id)
        return JsonResponse(resumo)
    except Http404:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)
    except Exception:
        logger.exception(ERRO_INTERNO_VIEW_PROJETO)
        return JsonResponse({'error': ERRO_INTERNO}, status=500)

@swagger_auto_schema(
    method='get',
    operation_summary='Lista materiais do projeto',
    operation_description='Retorna os materiais do projeto com suporte a paginacao e filtros por periodo e nome do material.',
    responses={
        200: resposta_sucesso('Lista paginada de materiais do projeto.', schema_paginada(MATERIAL_PROJETO_SCHEMA)),
        400: resposta_erro('Periodo ou parametros de filtro invalidos.'),
        404: resposta_erro('Projeto nao encontrado.'),
        500: resposta_erro('Erro interno ao listar materiais do projeto.'),
    },
)
@api_view(['GET'])
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
    except Exception:
        logger.exception(ERRO_INTERNO_VIEW_PROJETO)
        return JsonResponse({'error': ERRO_INTERNO}, status=500)


@swagger_auto_schema(
    method='get',
    operation_summary='Lista materiais disponiveis do projeto',
    operation_description='Retorna os materiais disponiveis para o projeto informado.',
    responses={
        200: resposta_sucesso('Lista de materiais disponiveis do projeto.', schema_array(MATERIAL_DISPONIVEL_SCHEMA)),
        500: resposta_erro('Erro interno ao listar materiais disponiveis do projeto.'),
    },
)
@api_view(['GET'])
@require_GET
def get_materiais_disponiveis_view(request, projeto_id):
    try:
        return JsonResponse(get_materiais_disponiveis(projeto_id), safe=False)
    except Exception as _:
        logger.exception(ERRO_INTERNO_VIEW_PROJETO)
        return JsonResponse({'error': ERRO_INTERNO}, status=500)
    
