from django.db.models import Sum
from ..models import Tarefa, TempoTarefa
from collections import defaultdict


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

def get_burnup_horas_projetos():
    registros = (
        TempoTarefa.objects
        .select_related('tarefa__projeto')
        .values(
            'tarefa__projeto__id',
            'tarefa__projeto__codigo_projeto',
            'tarefa__projeto__nome_projeto',
            'tarefa__projeto__status',
            'data'
        )
        .annotate(total_horas=Sum('horas_trabalhadas'))
        .order_by('tarefa__projeto__id', 'data')
    )

    projetos_map = defaultdict(list)

    for registro in registros:
        projeto_id = registro['tarefa__projeto__id']
        projeto_nome = registro['tarefa__projeto__nome_projeto']

        projetos_map[(projeto_id, projeto_nome)].append({
            'data': registro['data'].isoformat(),
            'horas': float(registro['total_horas'] or 0),
        })

    resultado = []

    for (projeto_id, codigo_projeto, projeto_nome, status), serie in projetos_map.items():
        acumulado = 0

        for ponto in serie:
            acumulado += ponto['horas']
            ponto['horas_acumuladas'] = acumulado

        resultado.append({
            "projeto_id": projeto.id,
            "codigo_projeto": projeto.codigo_projeto,
            "projeto": projeto.nome_projeto,
            "status": projeto.status,
            "serie": serie,
        })

    return resultado