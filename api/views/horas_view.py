from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..services.horas_svc import (get_horas_por_funcionario, get_burnup_horas_projetos)


@require_GET
def get_horas_por_funcionario_view(request, projeto_id):
    try:
        dados = get_horas_por_funcionario(projeto_id)
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@require_GET
def get_burnup_horas_projetos_view(request):
    try:
        dados = get_burnup_horas_projetos()
        return JsonResponse(dados, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)