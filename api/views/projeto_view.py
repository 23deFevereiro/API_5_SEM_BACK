from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..services.projeto_svc import (
    listar_projetos, 
    get_resumo_projeto, 
    get_materiais_projeto, 
    obter_dados_grafico_horas_acumuladas
)


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

@require_GET
def get_materiais_projeto_view(request, projeto_id):
    try:
        page = request.GET.get('page', 1)
        materiais = get_materiais_projeto(projeto_id, page=page, page_size=10)
        return JsonResponse(materiais)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def grafico_horas_investidas_view(request):
    try:
        dados_grafico = obter_dados_grafico_horas_acumuladas()
        return JsonResponse(dados_grafico, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)