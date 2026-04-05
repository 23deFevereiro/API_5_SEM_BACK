from math import ceil
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from ..models import Projeto, Tarefa, TempoTarefa, EstoqueMaterialProjeto, ComprasProjeto, EmpenhoMaterial


from django.db.models.functions import ExtractMonth, ExtractYear

def listar_projetos(search=''):
    projetos = Projeto.objects.all()
    if search:
        projetos = projetos.filter(nome_projeto__icontains=search)
    return list(projetos.values('id', 'codigo_projeto', 'nome_projeto'))


def get_overview_data_all():
    cost_material = Projeto.objects.select_related('empenho_material', 'empenho_material__material'
    ).filter(status='Em andamento', empenhomaterial__isnull=False
    ).annotate(
        month=ExtractMonth('empenhomaterial__data_empenho'),
        year=ExtractYear('empenhomaterial__data_empenho')
    ).values('codigo_projeto', 'nome_projeto', 'year', 'month'
    ).annotate(cost= Sum(F('empenhomaterial__quantidade_empenhada') * F('empenhomaterial__material__custo_estimado'))
    ).order_by('empenhomaterial__data_empenho')

    cost_list = []
    total_cost_dict = {}
    for material_data in list(cost_material):
        date_str = f'{material_data['month']:02d}/{material_data['year']}'
        
        date_group = [group for group in cost_list if group['date_str'] == date_str]
        if not date_group:
            date_group = { 'date_str': date_str, 'values': [] }
            cost_list.append(date_group)
        else: date_group = date_group[0]

        if material_data['codigo_projeto'] not in total_cost_dict:
            total_cost_dict[material_data['codigo_projeto']] = 0

        cost = total_cost_dict[material_data['codigo_projeto']] + float(material_data['cost'])
        total_cost_dict[material_data['codigo_projeto']] = cost

        date_group['values'].append(
            {
                'codigo_projeto': material_data['codigo_projeto'],
                'nome_projeto': material_data['nome_projeto'],
                'cost': cost
            }
        )

    return cost_list


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

def get_materiais_projeto(projeto_id, page=1, page_size=10):
    page = max(int(page), 1)

    materiais_qs = (
        EmpenhoMaterial.objects
        .filter(projeto_id=projeto_id)
        .values(
            'material_id',
            'material__descricao',
            'material__custo_estimado',
        )
        .annotate(
            quantidade=Sum('quantidade_empenhada')
        )
        .annotate(
            custo_total_estimado=ExpressionWrapper(
                F('quantidade') * F('material__custo_estimado'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
        .order_by('material__descricao')
    )

    total_items = materiais_qs.count()
    total_pages = ceil(total_items / page_size) if total_items > 0 else 1

    start = (page - 1) * page_size
    end = start + page_size

    resultados = list(materiais_qs[start:end])

    for item in resultados:
        item['nome_material'] = item.pop('material__descricao')
        item['custo_total_estimado'] = float(item['custo_total_estimado'] or 0)
        item.pop('material__custo_estimado', None)
        item.pop('material_id', None)

    return {
        'count': total_items,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': resultados,
    }