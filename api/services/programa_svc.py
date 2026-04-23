from decimal import Decimal
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.shortcuts import get_object_or_404
from ..models import Projeto, Tarefa, TempoTarefa, EmpenhoMaterial, ComprasProjeto

from ..models import DimPrograma

def listar_programas(search=''):
    programas = DimPrograma.objects.all()
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
