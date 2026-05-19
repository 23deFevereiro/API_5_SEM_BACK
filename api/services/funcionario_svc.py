from math import ceil
from django.db.models import Sum
from ..models import FatoHoras


def get_funcionarios_projeto(projeto_id, page=1, page_size=10, data_inicio=None, data_fim=None, funcionario=None):
    page = max(int(page), 1)

    base_qs = FatoHoras.objects.filter(projeto_id=projeto_id)
    if data_inicio:
        base_qs = base_qs.filter(tempo__data__gte=data_inicio)
    if data_fim:
        base_qs = base_qs.filter(tempo__data__lte=data_fim)
    if funcionario:
        base_qs = base_qs.filter(funcionario__nome__icontains=funcionario)

    funcionarios_qs = (
        base_qs
        .values('funcionario__nome')
        .annotate(total_horas=Sum('horas_trabalhadas'))
        .order_by('funcionario__nome')
    )

    total_items = funcionarios_qs.count()
    total_pages = ceil(total_items / page_size) if total_items > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size

    resultados = list(funcionarios_qs[start:end])

    for item in resultados:
        codigos = list(
            FatoHoras.objects
            .filter(funcionario__nome=item['funcionario__nome'])
            .values_list('projeto__codigo_projeto', flat=True)
            .distinct()
            .order_by('projeto__codigo_projeto')
        )

        item['funcionario'] = item.pop('funcionario__nome')
        item['total_horas'] = float(item['total_horas'] or 0)
        item['projetos'] = codigos

    return {
        'count': total_items,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': resultados,
    }
