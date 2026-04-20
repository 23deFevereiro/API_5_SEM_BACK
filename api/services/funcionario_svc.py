from math import ceil
from django.db.models import Sum
from ..models import Tarefa, TempoTarefa, Projeto


def get_funcionarios_projeto(projeto_id, page=1, page_size=10, data_inicio=None, data_fim=None, funcionario=None):
    page = max(int(page), 1)

    tarefas_ids = Tarefa.objects.filter(
        projeto_id=projeto_id
    ).values_list('id', flat=True)

    base_qs = TempoTarefa.objects.filter(tarefa_id__in=tarefas_ids)
    if data_inicio:
        base_qs = base_qs.filter(data__gte=data_inicio)
    if data_fim:
        base_qs = base_qs.filter(data__lte=data_fim)
    if funcionario:
        base_qs = base_qs.filter(usuario__icontains=funcionario)

    funcionarios_qs = (
        base_qs
        .values('usuario')
        .annotate(total_horas=Sum('horas_trabalhadas'))
        .order_by('usuario')
    )

    total_items = funcionarios_qs.count()
    total_pages = ceil(total_items / page_size) if total_items > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size

    resultados = list(funcionarios_qs[start:end])

    for item in resultados:
        projetos_ids = (
            TempoTarefa.objects
            .filter(usuario=item['usuario'])
            .values_list('tarefa__projeto_id', flat=True)
            .distinct()
        )

        codigos = list(
            Projeto.objects
            .filter(id__in=projetos_ids)
            .values_list('codigo_projeto', flat=True)
            .order_by('codigo_projeto')
        )

        item['total_horas'] = float(item['total_horas'] or 0)
        item['projetos'] = codigos

    return {
        'count': total_items,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': resultados,
    }
