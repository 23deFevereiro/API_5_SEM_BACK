from datetime import date

from drf_yasg import openapi

ERRO_INTERNO = 'Erro interno do servidor'
ERRO_INTERNO_VIEW_PROJETO = 'Erro interno na view de resumo do projeto'

ERRO_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING),
    },
    required=['error'],
)


def schema_array(item_schema):
    return openapi.Schema(type=openapi.TYPE_ARRAY, items=item_schema)


def schema_obj(properties, required=None):
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=properties,
        required=required or list(properties.keys()),
    )


def schema_paginada(item_schema):
    return schema_obj({
        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
        'page': openapi.Schema(type=openapi.TYPE_INTEGER),
        'page_size': openapi.Schema(type=openapi.TYPE_INTEGER),
        'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
        'results': schema_array(item_schema),
    })


def resposta_sucesso(description, schema):
    return openapi.Response(description=description, schema=schema)


def resposta_erro(description):
    return openapi.Response(description=description, schema=ERRO_SCHEMA)

def _parse_data(valor, nome_param):
    """Valida e converte uma string YYYY-MM-DD em date, ou None se ausente."""
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ValueError(f"Formato inválido para '{nome_param}': esperado YYYY-MM-DD")


def extrair_periodo(request):
    """Retorna (data_inicio, data_fim) das query params, ou None se ausentes/vazias."""
    data_inicio = _parse_data(request.GET.get('data_inicio'), 'data_inicio')
    data_fim = _parse_data(request.GET.get('data_fim'), 'data_fim')
    return data_inicio, data_fim
