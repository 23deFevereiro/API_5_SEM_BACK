from django.db.models import Sum
from ..models import Tarefa, TempoTarefa


def get_horas_por_funcionario(projeto_id):
    
    tarefas_ids = Tarefa.objects.filter(
        projeto_id=projeto_id
    ).values_list('id', flat=True)

    registros = (
        TempoTarefa.objects
        .filter(tarefa_id__in=tarefas_ids)
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