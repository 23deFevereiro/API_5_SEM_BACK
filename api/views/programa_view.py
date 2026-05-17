from drf_yasg import openapi
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from ..services.programa_svc import (
    listar_programas,
    get_resumo_programa,
    get_distribuicao_status,
    get_burnup_horas_programas,
    get_burnup_custo_programas,
    get_tabela_projetos,
    get_horas_por_projeto,
)
from .view_utils import resposta_erro, resposta_sucesso, schema_array, schema_obj, schema_paginada

_PROGRAMA_NAO_ENCONTRADO = 'Programa não encontrado'

PROGRAMA_SCHEMA = schema_obj({
    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
    'codigo_programa': openapi.Schema(type=openapi.TYPE_STRING),
    'nome_programa': openapi.Schema(type=openapi.TYPE_STRING),
})

RESUMO_PROGRAMA_SCHEMA = schema_obj({
    'total_projetos': openapi.Schema(type=openapi.TYPE_INTEGER),
    'horas_estimadas': openapi.Schema(type=openapi.TYPE_NUMBER),
    'horas_realizadas': openapi.Schema(type=openapi.TYPE_NUMBER),
    'custo_estimado': openapi.Schema(type=openapi.TYPE_NUMBER),
    'custo_real': openapi.Schema(type=openapi.TYPE_NUMBER),
})

STATUS_PROGRAMA_SCHEMA = schema_obj({
    'status': openapi.Schema(type=openapi.TYPE_STRING),
    'quantidade': openapi.Schema(type=openapi.TYPE_INTEGER),
    'percentual': openapi.Schema(type=openapi.TYPE_NUMBER),
    'cor': openapi.Schema(type=openapi.TYPE_STRING),
})

DISTRIBUICAO_STATUS_SCHEMA = schema_obj({
    'total': openapi.Schema(type=openapi.TYPE_INTEGER),
    'status': schema_array(STATUS_PROGRAMA_SCHEMA),
})

BURNUP_HORAS_PROGRAMA_VALUE_SCHEMA = schema_obj({
    'codigo_programa': openapi.Schema(type=openapi.TYPE_STRING),
    'nome_programa': openapi.Schema(type=openapi.TYPE_STRING),
    'horas': openapi.Schema(type=openapi.TYPE_NUMBER),
})

BURNUP_CUSTO_PROGRAMA_VALUE_SCHEMA = schema_obj({
    'codigo_programa': openapi.Schema(type=openapi.TYPE_STRING),
    'nome_programa': openapi.Schema(type=openapi.TYPE_STRING),
    'custo': openapi.Schema(type=openapi.TYPE_NUMBER),
})

BURNUP_GRUPO_HORAS_SCHEMA = schema_obj({
    'date_str': openapi.Schema(type=openapi.TYPE_STRING),
    'values': schema_array(BURNUP_HORAS_PROGRAMA_VALUE_SCHEMA),
})

BURNUP_GRUPO_CUSTO_SCHEMA = schema_obj({
    'date_str': openapi.Schema(type=openapi.TYPE_STRING),
    'values': schema_array(BURNUP_CUSTO_PROGRAMA_VALUE_SCHEMA),
})

HORAS_PROJETO_SCHEMA = schema_obj({
    'nome_projeto': openapi.Schema(type=openapi.TYPE_STRING),
    'horas_realizadas': openapi.Schema(type=openapi.TYPE_NUMBER),
})

TABELA_PROJETO_ITEM_SCHEMA = schema_obj({
    'nome_projeto': openapi.Schema(type=openapi.TYPE_STRING),
    'responsavel': openapi.Schema(type=openapi.TYPE_STRING),
    'status': openapi.Schema(type=openapi.TYPE_STRING),
    'horas_estimadas': openapi.Schema(type=openapi.TYPE_NUMBER),
    'horas_realizadas': openapi.Schema(type=openapi.TYPE_NUMBER),
    'total_tarefas': openapi.Schema(type=openapi.TYPE_INTEGER),
    'tarefas_concluidas': openapi.Schema(type=openapi.TYPE_INTEGER),
    'percentual_tarefas_concluidas': openapi.Schema(type=openapi.TYPE_NUMBER),
    'desvio_horas': openapi.Schema(type=openapi.TYPE_NUMBER),
    'percentual_desvio': openapi.Schema(type=openapi.TYPE_NUMBER),
    'data_ultima_atividade': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
    'dias_desde_ultima_atividade': openapi.Schema(type=openapi.TYPE_INTEGER),
    'dentro_do_prazo': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    'sem_horas_registradas': openapi.Schema(type=openapi.TYPE_BOOLEAN),
    'acao': openapi.Schema(type=openapi.TYPE_STRING),
})


@swagger_auto_schema(
    method='get',
    operation_summary='Lista programas',
    operation_description='Retorna a lista de programas cadastrados com filtro textual opcional pelo parametro search.',
    responses={
        200: resposta_sucesso('Lista de programas cadastrados.', schema_array(PROGRAMA_SCHEMA)),
    },
)
@api_view(['GET'])
@require_GET
def listar_programas_view(request):
    search = request.GET.get('search', '')
    programas = listar_programas(search)
    return JsonResponse(programas, safe=False)


@swagger_auto_schema(
    method='get',
    operation_summary='Consulta resumo do programa',
    operation_description='Retorna o resumo consolidado do programa informado pelo identificador na URL.',
    responses={
        200: resposta_sucesso('Resumo consolidado do programa.', RESUMO_PROGRAMA_SCHEMA),
        404: resposta_erro('Programa nao encontrado.'),
        500: resposta_erro('Erro interno ao buscar resumo do programa.'),
    },
)
@api_view(['GET'])
@require_GET
def get_resumo_programa_view(request, programa_id):
    try:
        resumo = get_resumo_programa(programa_id)
        return JsonResponse(resumo)
    except Http404:
        return JsonResponse({'error': _PROGRAMA_NAO_ENCONTRADO}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@swagger_auto_schema(
    method='get',
    operation_summary='Consulta distribuicao de status do programa',
    operation_description='Retorna a distribuicao de status dos projetos associados ao programa informado.',
    responses={
        200: resposta_sucesso('Distribuicao de status dos projetos do programa.', DISTRIBUICAO_STATUS_SCHEMA),
        500: resposta_erro('Erro interno ao buscar distribuicao de status do programa.'),
    },
)
@api_view(['GET'])
@require_GET
def get_distribuicao_status_view(request, programa_id):
    try:
        dados = get_distribuicao_status(programa_id)
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@swagger_auto_schema(
    method='get',
    operation_summary='Consulta burnup de horas dos programas',
    operation_description='Retorna os dados consolidados de burnup de horas considerando todos os programas.',
    responses={
        200: resposta_sucesso('Serie temporal acumulada de horas por programa.', schema_array(BURNUP_GRUPO_HORAS_SCHEMA)),
        500: resposta_erro('Erro interno ao buscar burnup de horas dos programas.'),
    },
)
@api_view(['GET'])
@require_GET
def get_burnup_horas_programas_view(request):
    try:
        dados = get_burnup_horas_programas()
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@swagger_auto_schema(
    method='get',
    operation_summary='Consulta burnup de custo dos programas',
    operation_description='Retorna os dados consolidados de burnup de custo considerando todos os programas.',
    responses={
        200: resposta_sucesso('Serie temporal acumulada de custo por programa.', schema_array(BURNUP_GRUPO_CUSTO_SCHEMA)),
        500: resposta_erro('Erro interno ao buscar burnup de custo dos programas.'),
    },
)
@api_view(['GET'])
@require_GET
def get_burnup_custo_programas_view(request):
    try:
        dados = get_burnup_custo_programas()
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@swagger_auto_schema(
    method='get',
    operation_summary='Consulta horas por projeto no programa',
    operation_description='Retorna as horas consolidadas por projeto dentro do programa informado.',
    responses={
        200: resposta_sucesso('Horas realizadas por projeto do programa.', schema_array(HORAS_PROJETO_SCHEMA)),
        404: resposta_erro('Programa nao encontrado.'),
        500: resposta_erro('Erro interno ao buscar horas por projeto do programa.'),
    },
)
@api_view(['GET'])
@require_GET
def get_horas_por_projeto_view(request, programa_id):
    try:
        dados = get_horas_por_projeto(programa_id)
        return JsonResponse(dados, safe=False)
    except Http404:
        return JsonResponse({'error': _PROGRAMA_NAO_ENCONTRADO}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@swagger_auto_schema(
    method='get',
    operation_summary='Consulta tabela de projetos do programa',
    operation_description='Retorna a tabela paginada de projetos do programa com ordenacao pelos campos suportados pela API.',
    responses={
        200: resposta_sucesso('Tabela paginada dos projetos do programa.', schema_paginada(TABELA_PROJETO_ITEM_SCHEMA)),
        400: resposta_erro('Parametros de paginacao ou ordenacao invalidos.'),
        404: resposta_erro('Programa nao encontrado.'),
        500: resposta_erro('Erro interno ao buscar tabela de projetos do programa.'),
    },
)
@api_view(['GET'])
@require_GET
def get_tabela_projetos_view(request, programa_id):
    try:
        page = request.GET.get('page', 1)
        sort_by = request.GET.get('sort_by', 'nome_projeto')
        sort_dir = request.GET.get('sort_dir', 'asc')
        if sort_by not in ('nome_projeto', 'responsavel', 'status', 'situacao'):
            sort_by = 'nome_projeto'
        if sort_dir not in ('asc', 'desc'):
            sort_dir = 'asc'
        dados = get_tabela_projetos(programa_id, page=page, page_size=10, sort_by=sort_by, sort_dir=sort_dir)
        return JsonResponse(dados)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Http404:
        return JsonResponse({'error': _PROGRAMA_NAO_ENCONTRADO}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
