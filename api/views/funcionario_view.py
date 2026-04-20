from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..services.funcionario_svc import get_funcionarios_projeto


@require_GET
def get_funcionarios_projeto_view(request, projeto_id):
    try:
        page = request.GET.get('page', 1)
        data_inicio = request.GET.get('data_inicio') or None
        data_fim = request.GET.get('data_fim') or None
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
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
