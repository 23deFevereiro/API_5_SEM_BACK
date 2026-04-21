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
            'data': registro['data'],
            'horas': float(registro['total_horas'] or 0),
        })

    resultado = []

    for (projeto_id, projeto_nome), serie in projetos_map.items():
        acumulado = 0

        if not serie:
            resultado.append({
                "projeto_id": projeto_id,
                "projeto": projeto_nome,
                "serie": [],
            })
            continue

        data_inicial = serie[0]['data']

        for ponto in serie:
            acumulado += ponto['horas']

            diferenca_dias = (ponto['data'] - data_inicial).days
            numero_semana = (diferenca_dias // 7) + 1

            ponto['semana'] = f"Semana {numero_semana}"
            ponto['horas_acumuladas'] = acumulado
            ponto['data'] = ponto['data'].isoformat()

        resultado.append({
            "projeto_id": projeto_id,
            "projeto": projeto_nome,
            "serie": serie,
        })

    return resultado