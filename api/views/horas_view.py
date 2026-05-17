import logging

from drf_yasg import openapi
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from ..services.horas_svc import (get_horas_por_funcionario, get_burnup_horas_projetos)

from .view_utils import ERRO_INTERNO, extrair_periodo, resposta_erro, resposta_sucesso, schema_array, schema_obj
from ..services.horas_svc import get_horas_por_funcionario, get_nomes_funcionarios_projeto

logger = logging.getLogger(__name__)

HORAS_FUNCIONARIO_SCHEMA = schema_obj({
    'funcionario': openapi.Schema(type=openapi.TYPE_STRING),
    'total_horas': openapi.Schema(type=openapi.TYPE_NUMBER),
})

BURNUP_SERIE_SCHEMA = schema_obj({
    'mes': openapi.Schema(type=openapi.TYPE_STRING),
    'horas': openapi.Schema(type=openapi.TYPE_NUMBER),
    'horas_acumuladas': openapi.Schema(type=openapi.TYPE_NUMBER),
})

BURNUP_PROJETO_SCHEMA = schema_obj({
    'projeto_id': openapi.Schema(type=openapi.TYPE_INTEGER),
    'projeto': openapi.Schema(type=openapi.TYPE_STRING),
    'serie': schema_array(BURNUP_SERIE_SCHEMA),
})


@swagger_auto_schema(
    method='get',
    operation_summary='Consulta horas por funcionario',
    operation_description='Retorna as horas apontadas por funcionario em um projeto, com filtros opcionais por periodo e nome do funcionario.',
    responses={
        200: resposta_sucesso('Horas consolidadas por funcionario do projeto.', schema_array(HORAS_FUNCIONARIO_SCHEMA)),
        400: resposta_erro('Periodo informado em formato invalido.'),
        500: resposta_erro('Erro interno ao buscar horas por funcionario.'),
    },
)
@api_view(['GET'])
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
        return JsonResponse({'error': str(e)}, status=500)
    
@swagger_auto_schema(
    method='get',
    operation_summary='Consulta burnup de horas dos projetos',
    operation_description='Retorna os dados consolidados de burnup de horas dos projetos, podendo filtrar os resultados pelo parametro programa_id.',
    responses={
        200: resposta_sucesso('Serie temporal de burnup de horas por projeto.', schema_array(BURNUP_PROJETO_SCHEMA)),
        500: resposta_erro('Erro interno ao buscar burnup de horas dos projetos.'),
    },
)
@api_view(['GET'])
@require_GET
def get_burnup_horas_projetos_view(request):
    try:
        programa_id = request.GET.get('programa_id')
        programa_id = int(programa_id) if programa_id else None
        dados = get_burnup_horas_projetos(programa_id=programa_id)
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@swagger_auto_schema(
    method='get',
    operation_summary='Lista nomes dos funcionarios do projeto',
    operation_description='Retorna os nomes dos funcionarios vinculados ao projeto informado.',
    responses={
        200: resposta_sucesso('Lista de nomes dos funcionarios do projeto.', schema_array(openapi.Schema(type=openapi.TYPE_STRING))),
        500: resposta_erro('Erro interno ao listar nomes dos funcionarios do projeto.'),
    },
)
@api_view(['GET'])
@require_GET
def get_nomes_funcionarios_view(request, projeto_id):
    try:
        return JsonResponse(get_nomes_funcionarios_projeto(projeto_id), safe=False)
    except Exception as _:
        logger.exception('Erro interno na view de horas')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)
