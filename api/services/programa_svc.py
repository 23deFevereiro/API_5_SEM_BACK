from decimal import Decimal
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Count
from django.shortcuts import get_object_or_404
from ..models import DimPrograma, DimProjeto, DimTarefa, FatoHoras, FatoMateriais, FatoCompras

STATUS_PADRAO = [
    'Planejamento',
    'Em andamento',
    'Suspenso',
    'Concluído',
]

STATUS_CORES = {
    'Planejamento': '#3B82F6',
    'Em andamento': '#EAB308',
    'Suspenso': '#F97316',
    'Concluído': '#22C55E',
}


def listar_programas(search=''):
    programas = DimPrograma.objects.all()
    if search:
        programas = programas.filter(nome_programa__icontains=search)
    return list(programas.values('id', 'codigo_programa', 'nome_programa'))


def get_resumo_programa(programa_id):
    get_object_or_404(DimPrograma, id=programa_id)

    projetos_ids = DimProjeto.objects.filter(
        programa_id=programa_id
    ).values_list('id', flat=True)

    total_projetos = len(projetos_ids)

    horas_estimadas = DimTarefa.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(
        total=Sum('horas_estimadas')
    )['total'] or Decimal('0')

    horas_realizadas = FatoHoras.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(
        total=Sum('horas_trabalhadas')
    )['total'] or Decimal('0')

    custo_estimado_mao_de_obra = FatoHoras.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(
        total=Sum('custo_horas')
    )['total'] or Decimal('0')

    custo_estimado_materiais = FatoMateriais.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(
        total=Sum('custo_materiais')
    )['total'] or Decimal('0')

    custo_estimado = custo_estimado_mao_de_obra + custo_estimado_materiais

    custo_real_mao_de_obra = FatoHoras.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(
        total=Sum('custo_horas')
    )['total'] or Decimal('0')

    custo_real_materiais = FatoCompras.objects.filter(
        projeto_id__in=projetos_ids
    ).exclude(
        status__nome_status='Cancelado'
    ).aggregate(
        total=Sum('valor_alocado')
    )['total'] or Decimal('0')

    custo_real = custo_real_mao_de_obra + custo_real_materiais

    return {
        'total_projetos': total_projetos,
        'horas_estimadas': horas_estimadas,
        'horas_realizadas': horas_realizadas,
        'custo_estimado': custo_estimado,
        'custo_real': custo_real,
    }


def get_distribuicao_status(programa_id):
    status_counts = list(
        DimProjeto.objects
        .filter(programa_id=programa_id)
        .values('status')
        .annotate(total=Count('id'))
    )

    status_dict = {item['status']: item['total'] for item in status_counts}
    total_geral = sum(item['total'] for item in status_counts)

    resultado = []
    for status in STATUS_PADRAO:
        quantidade = status_dict.get(status, 0)
        percentual = round((quantidade / total_geral) * 100, 1) if total_geral > 0 else 0
        resultado.append({
            'status': status,
            'quantidade': quantidade,
            'percentual': percentual,
            'cor': STATUS_CORES[status],
        })

    resultado = [r for r in resultado if r['quantidade'] > 0]

    return {
        'total': total_geral,
        'status': resultado,
    }


def get_burnup_horas_programas():
    horas_qs = (
        FatoHoras.objects
        .values(
            'programa__codigo_programa',
            'programa__nome_programa',
            'tempo__ano',
            'tempo__mes',
        )
        .annotate(horas_periodo=Sum('horas_trabalhadas'))
        .order_by('tempo__ano', 'tempo__mes')
    )
    
    grupos_por_data = {}
    horas_acumuladas = {}
    for row in horas_qs:
        codigo = row['programa__codigo_programa']
        nome = row['programa__nome_programa']
        date_str = f'{row["tempo__mes"]:02d}/{row["tempo__ano"]}'

        date_group = grupos_por_data.get(date_str)
        if date_group is None:
            date_group = {'date_str': date_str, 'values': []}
            grupos_por_data[date_str] = date_group

        horas = horas_acumuladas.get(codigo, 0.0) + float(row['horas_periodo'] or 0)
        horas_acumuladas[codigo] = horas

        date_group['values'].append({
            'codigo_programa': codigo,
            'nome_programa': nome,
            'horas': horas,
        })

    return list(grupos_por_data.values())
