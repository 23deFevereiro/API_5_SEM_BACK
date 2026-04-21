from ..services.programa_svc import listar_programas
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def listar_programas_view(request):
    search = request.GET.get('search', '')
    programas = listar_programas(search)
    return JsonResponse(programas, safe=False)