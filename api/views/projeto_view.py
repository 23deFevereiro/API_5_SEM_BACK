from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..services.projeto_svc import listar_projetos, get_resumo_projeto


@require_GET
def listar_projetos_view(request):
    search = request.GET.get('search', '')
    projetos = listar_projetos(search)
    return JsonResponse(projetos, safe=False)


@require_GET
def get_resumo_projeto_view(request, projeto_id):
    try:
        resumo = get_resumo_projeto(projeto_id)
        return JsonResponse(resumo)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
