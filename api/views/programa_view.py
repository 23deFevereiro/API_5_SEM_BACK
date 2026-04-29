from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from ..services.programa_svc import (
    listar_programas,
    get_resumo_programa,
    get_distribuicao_status,
    get_burnup_horas_programas,
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