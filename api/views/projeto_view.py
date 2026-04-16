from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from ..services.projeto_svc import listar_projetos, get_resumo_projeto, get_materiais_projeto, get_overview_data_all

@require_GET
def get_overview_projetos(request):
    return JsonResponse(get_overview_data_all(), safe=False)

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
    except Http404:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_materiais_projeto_view(request, projeto_id):
    try:
        page = request.GET.get('page', 1)
        materiais = get_materiais_projeto(projeto_id, page=page, page_size=10)
        return JsonResponse(materiais)
    except Http404:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)