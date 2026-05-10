from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from ..services.programa_svc import (
    listar_programas,
    get_resumo_programa,
    get_distribuicao_status,
    get_burnup_horas_programas,
    get_burnup_custo_programas,
    get_tabela_projetos,
    get_horas_por_projeto,
)


@require_GET
def listar_programas_view(request):
    search = request.GET.get('search', '')
    programas = listar_programas(search)
    return JsonResponse(programas, safe=False)


@require_GET
def get_resumo_programa_view(request, programa_id):
    try:
        resumo = get_resumo_programa(programa_id)
        return JsonResponse(resumo)
    except Http404:
        return JsonResponse({'error': 'Programa não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def get_distribuicao_status_view(request, programa_id):
    try:
        dados = get_distribuicao_status(programa_id)
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def get_burnup_horas_programas_view(request):
    try:
        dados = get_burnup_horas_programas()
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def get_burnup_custo_programas_view(request):
    try:
        dados = get_burnup_custo_programas()
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def get_horas_por_projeto_view(request, programa_id):
    try:
        dados = get_horas_por_projeto(programa_id)
        return JsonResponse(dados, safe=False)
    except Http404:
        return JsonResponse({'error': 'Programa não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def get_tabela_projetos_view(request, programa_id):
    try:
        page = request.GET.get('page', 1)
        sort_by = request.GET.get('sort_by', 'nome_projeto')
        sort_dir = request.GET.get('sort_dir', 'asc')
        if sort_by not in ('nome_projeto', 'responsavel', 'status', 'acao'):
            sort_by = 'nome_projeto'
        if sort_dir not in ('asc', 'desc'):
            sort_dir = 'asc'
        dados = get_tabela_projetos(programa_id, page=page, page_size=10, sort_by=sort_by, sort_dir=sort_dir)
        return JsonResponse(dados)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Http404:
        return JsonResponse({'error': 'Programa não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
