from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..services.horas_svc import get_horas_por_funcionario, get_nomes_funcionarios_projeto


@require_GET
def get_horas_por_funcionario_view(request, projeto_id):
    try:
        data_inicio = request.GET.get('data_inicio') or None
        data_fim = request.GET.get('data_fim') or None
        funcionario = request.GET.get('funcionario') or None
        dados = get_horas_por_funcionario(
            projeto_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            funcionario=funcionario,
        )
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def get_nomes_funcionarios_view(request, projeto_id):
    try:
        return JsonResponse(get_nomes_funcionarios_projeto(projeto_id), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
