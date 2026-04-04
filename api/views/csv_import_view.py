from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from ..services.csv_import_svc import import_csv, import_all_csvs, get_available_models


@csrf_exempt
@require_POST
def csv_import_view(request):
    model_name = request.POST.get('model', '').strip()
    csv_file = request.FILES.get('file')

    if not model_name:
        return JsonResponse(
            {'error': f"'model' parameter is required. Available: {', '.join(get_available_models())}"},
            status=400,
        )

    if not csv_file:
        return JsonResponse({'error': "'file' is required"}, status=400)

    if not csv_file.name.endswith('.csv'):
        return JsonResponse({'error': 'File must be a .csv'}, status=400)

    try:
        file_content = csv_file.read()
        result = import_csv(model_name, file_content)
        return JsonResponse(result)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def csv_import_all_view(request):
    try:
        results = import_all_csvs()
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
