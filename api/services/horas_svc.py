from django.db.models import Sum
from ..models import FatoHoras


def get_horas_por_funcionario(projeto_id, data_inicio=None, data_fim=None, funcionario=None):
    registros_qs = FatoHoras.objects.filter(projeto_id=projeto_id)
    if data_inicio:
        registros_qs = registros_qs.filter(tempo__data__gte=data_inicio)
    if data_fim:
        registros_qs = registros_qs.filter(tempo__data__lte=data_fim)
    if funcionario:
        registros_qs = registros_qs.filter(funcionario__nome__icontains=funcionario)

    registros = (
        registros_qs
        .values('funcionario__nome')
        .annotate(total_horas=Sum('horas_trabalhadas'))
        .order_by('funcionario__nome')
    )

    return [
        {
            'funcionario': r['funcionario__nome'],
            'total_horas': float(r['total_horas'] or 0),
        }
        for r in registros
    ]

def get_nomes_funcionarios_projeto(projeto_id):
    return sorted(
        FatoHoras.objects
        .filter(projeto_id=projeto_id)
        .values_list('funcionario__nome', flat=True)
        .order_by('funcionario__nome')
        .distinct()
    )

def get_burnup_horas_projetos():
    registros = (
        TempoTarefa.objects
        .select_related('tarefa__projeto')
        .filter(tarefa__projeto__status='Em andamento')
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
        projeto_nome = registro['tarefa__projeto__codigo_projeto']

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

        semanas_map = defaultdict(float)

        for ponto in serie:
            diferenca_dias = (ponto['data'] - data_inicial).days
            numero_semana = (diferenca_dias // 7) + 1

            if numero_semana >= 4:
                numero_semana = 4

            semanas_map[numero_semana] += ponto['horas']
        
        ultima_semana = max(semanas_map.keys(), default=0)

        serie_final = []
        acumulado = 0

        for numero_semana in range(1, ultima_semana + 1):
            horas_semana = semanas_map[numero_semana]
            acumulado += horas_semana

            nome_semana = f"Semana {numero_semana}" if numero_semana < 4 else "Semana 4+"

            serie_final.append({
                "semana": nome_semana,
                "horas": horas_semana,
                "horas_acumuladas": acumulado,
            })

        resultado.append({
            "projeto_id": projeto_id,
            "projeto": projeto_nome,
            "serie": serie_final,
        })

    return resultado


