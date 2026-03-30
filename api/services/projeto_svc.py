from django.db.models import Sum, F
from ..models import Projeto, Tarefa, TempoTarefa, EstoqueMaterialProjeto, ComprasProjeto


def listar_projetos(search=''):
    projetos = Projeto.objects.all()
    if search:
        projetos = projetos.filter(nome_projeto__icontains=search)
    return list(projetos.values('id', 'codigo_projeto', 'nome_projeto'))


def get_resumo_projeto(projeto_id):
    custo_materiais = EstoqueMaterialProjeto.objects.filter(
        projeto_id=projeto_id
    ).annotate(
        custo_total=F('quantidade') * F('material__custo_estimado')
    ).aggregate(total=Sum('custo_total'))

    custo_compras = ComprasProjeto.objects.filter(
        projeto_id=projeto_id
    ).exclude(
        pedido_compra__status='Cancelado'
    ).aggregate(total=Sum('valor_alocado'))

    tarefas_ids = Tarefa.objects.filter(
        projeto_id=projeto_id
    ).values_list('id', flat=True)

    tempo_total = TempoTarefa.objects.filter(
        tarefa_id__in=tarefas_ids
    ).aggregate(total=Sum('horas_trabalhadas'))

    return {
        'custo_materiais': float(custo_materiais['total'] or 0),
        'custo_compras': float(custo_compras['total'] or 0),
        'tempo_total': float(tempo_total['total'] or 0),
    }
