from django.http import JsonResponse
from ..services.projeto_svc import listar_projetos, get_resumo_projeto


def listar_projetos_view(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Metodo nao permitido'}, status=405)

    search = request.GET.get('search', '')
    projetos = listar_projetos(search)
    return JsonResponse(projetos, safe=False)


def get_resumo_projeto_view(request, projeto_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Metodo nao permitido'}, status=405)

    try:
        resumo = get_resumo_projeto(projeto_id)
        return JsonResponse(resumo)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
