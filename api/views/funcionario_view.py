from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..services.funcionario_svc import get_funcionarios_projeto


@require_GET
def get_funcionarios_projeto_view(request, projeto_id):
    try:
        page = request.GET.get('page', 1)
        funcionarios = get_funcionarios_projeto(projeto_id, page=page, page_size=10)
        return JsonResponse(funcionarios)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)