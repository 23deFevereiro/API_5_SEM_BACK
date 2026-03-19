from ..services.demo_svc import get_demo
from django.http import JsonResponse

def get_demo_view(request):
	return JsonResponse(get_demo(), safe=False)