import logging

from drf_yasg import openapi
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema

from .view_utils import ERRO_INTERNO, extrair_periodo, resposta_erro, resposta_sucesso, schema_array, schema_obj, schema_paginada
from ..services.funcionario_svc import get_funcionarios_projeto

logger = logging.getLogger(__name__)

FUNCIONARIO_PROJETO_SCHEMA = schema_obj({
    'funcionario': openapi.Schema(type=openapi.TYPE_STRING),
    'total_horas': openapi.Schema(type=openapi.TYPE_NUMBER),
    'projetos': schema_array(openapi.Schema(type=openapi.TYPE_STRING)),
})


@swagger_auto_schema(
    method='get',
    operation_summary='Lista funcionarios do projeto',
    operation_description='Retorna os funcionarios associados a um projeto com suporte a paginacao e filtros por periodo e nome do funcionario.',
    responses={
        200: resposta_sucesso('Lista paginada de funcionarios do projeto.', schema_paginada(FUNCIONARIO_PROJETO_SCHEMA)),
        400: resposta_erro('Periodo informado em formato invalido.'),
        500: resposta_erro('Erro interno ao listar funcionarios do projeto.'),
    },
)
@api_view(['GET'])
@require_GET
def get_funcionarios_projeto_view(request, projeto_id):
    try:
        page = request.GET.get('page', 1)
        data_inicio, data_fim = extrair_periodo(request)
        funcionario = request.GET.get('funcionario') or None
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
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.exception('Erro interno na view de funcionário')
        return JsonResponse({'error': ERRO_INTERNO}, status=500)
