from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..services.horas_svc import get_horas_por_funcionario


@require_GET
def get_horas_por_funcionario_view(request, projeto_id):
    try:
        dados = get_horas_por_funcionario(projeto_id)
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)