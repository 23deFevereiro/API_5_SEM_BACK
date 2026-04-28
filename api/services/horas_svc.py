from collections import defaultdict

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
        FatoHoras.objects
        .filter(projeto__status='Em andamento')
        .values(
            'projeto__id',
            'projeto__codigo_projeto',
            'tempo__ano',
            'tempo__mes',
        )
        .annotate(total_horas=Sum('horas_trabalhadas'))
        .order_by('projeto__id', 'tempo__ano', 'tempo__mes')
    )

    projetos_map = defaultdict(list)

    for registro in registros:
        projeto_id = registro['projeto__id']
        projeto_nome = registro['projeto__codigo_projeto']
        mes_str = f"{registro['tempo__mes']:02d}/{registro['tempo__ano']}"

        projetos_map[(projeto_id, projeto_nome)].append({
            'mes': mes_str,
            'horas': float(registro['total_horas'] or 0),
        })

    resultado = []

    for (projeto_id, projeto_nome), serie in projetos_map.items():
        acumulado = 0
        serie_final = []

        for ponto in serie:
            acumulado += ponto['horas']
            serie_final.append({
                "mes": ponto['mes'],
                "horas": ponto['horas'],
                "horas_acumuladas": acumulado,
            })

        resultado.append({
            "projeto_id": projeto_id,
            "projeto": projeto_nome,
            "serie": serie_final,
        })

    return resultado
