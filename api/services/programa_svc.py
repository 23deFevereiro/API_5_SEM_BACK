from decimal import Decimal
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Count
from django.shortcuts import get_object_or_404
from ..models import Projeto, Tarefa, TempoTarefa, EmpenhoMaterial, ComprasProjeto

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
    from ..models import Programa
    programas = Programa.objects.all()
    if search:
        programas = programas.filter(nome_programa__icontains=search)
    return list(programas.values('id', 'codigo_programa', 'nome_programa'))


def get_resumo_programa(programa_id):
    from ..models import Programa
    get_object_or_404(Programa, id=programa_id)

    projetos_ids = Projeto.objects.filter(
        programa_id=programa_id
    ).values_list('id', flat=True)

    total_projetos = len(projetos_ids)

    horas_estimadas = Tarefa.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(
        total=Sum('estimativa_horas')
    )['total'] or Decimal('0')

    horas_realizadas = TempoTarefa.objects.filter(
        tarefa__projeto_id__in=projetos_ids
    ).aggregate(
        total=Sum('horas_trabalhadas')
    )['total'] or Decimal('0')

    custo_estimado_mao_de_obra = Tarefa.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('estimativa_horas') * F('projeto__custo_hora'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
    )['total'] or Decimal('0')

    custo_estimado_materiais = EmpenhoMaterial.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantidade_empenhada') * F('material__custo_estimado'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
    )['total'] or Decimal('0')

    custo_estimado = custo_estimado_mao_de_obra + custo_estimado_materiais

    custo_real_mao_de_obra = TempoTarefa.objects.filter(
        tarefa__projeto_id__in=projetos_ids
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('horas_trabalhadas') * F('tarefa__projeto__custo_hora'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
    )['total'] or Decimal('0')

    custo_real_materiais = ComprasProjeto.objects.filter(
        projeto_id__in=projetos_ids
    ).exclude(
        pedido_compra__status='Cancelado'
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
        Projeto.objects
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