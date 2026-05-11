from datetime import date

ERRO_INTERNO = "Erro interno do servidor"
ERRO_INTERNO_VIEW_PROJETO = "Erro interno na view de resumo do projeto"


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
    data_inicio = _parse_data(request.GET.get("data_inicio"), "data_inicio")
    data_fim = _parse_data(request.GET.get("data_fim"), "data_fim")
    return data_inicio, data_fim
