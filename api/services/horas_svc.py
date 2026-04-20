from django.db.models import Sum
from ..models import Tarefa, TempoTarefa


def get_horas_por_funcionario(projeto_id, data_inicio=None, data_fim=None, funcionario=None):

    tarefas_ids = Tarefa.objects.filter(
        projeto_id=projeto_id
    ).values_list('id', flat=True)

    registros_qs = TempoTarefa.objects.filter(tarefa_id__in=tarefas_ids)
    if data_inicio:
        registros_qs = registros_qs.filter(data__gte=data_inicio)
    if data_fim:
        registros_qs = registros_qs.filter(data__lte=data_fim)
    if funcionario:
        registros_qs = registros_qs.filter(usuario__icontains=funcionario)

    registros = (
        registros_qs
        .values('usuario')
        .annotate(total_horas=Sum('horas_trabalhadas'))
        .order_by('usuario')
    )

    return [
        {
            'funcionario': r['usuario'],
            'total_horas': float(r['total_horas'] or 0),
        }
        for r in registros
    ]


def get_nomes_funcionarios_projeto(projeto_id):
    tarefas_ids = Tarefa.objects.filter(
        projeto_id=projeto_id
    ).values_list('id', flat=True)

    return sorted(
        TempoTarefa.objects
        .filter(tarefa_id__in=tarefas_ids)
        .values_list('usuario', flat=True)
        .distinct()
    )
