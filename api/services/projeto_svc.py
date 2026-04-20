from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.db.models.functions import ExtractMonth, ExtractYear
from decimal import Decimal
from django.shortcuts import get_object_or_404
from ..models import Projeto, Tarefa, TempoTarefa, EstoqueMaterialProjeto, ComprasProjeto, EmpenhoMaterial
from ..utils.pagination import normalizar_pagina, calcular_paginacao


def listar_projetos(search='', programa_id=None):
    projetos = Projeto.objects.all()
    if search:
        projetos = projetos.filter(nome_projeto__icontains=search)
    if programa_id:
        projetos = projetos.filter(programa=programa_id)
    return list(projetos.values('id', 'codigo_projeto', 'nome_projeto'))


def get_overview_data_all(programa_id=None):
    projetos = Projeto.objects.all()
    if programa_id:
        projetos = projetos.filter(programa=programa_id)
    
    cost_material = projetos.select_related('empenho_material', 'empenho_material__material'
    ).filter(status='Em andamento', empenhomaterial__isnull=False
    ).annotate(
        month=ExtractMonth('empenhomaterial__data_empenho'),
        year=ExtractYear('empenhomaterial__data_empenho')
    ).values('codigo_projeto', 'nome_projeto', 'year', 'month'
    ).annotate(cost=Sum(F('empenhomaterial__quantidade_empenhada') * F('empenhomaterial__material__custo_estimado'))
    ).order_by('empenhomaterial__data_empenho')

    cost_list = []
    total_cost_dict = {}
    for material_data in list(cost_material):
        date_str = f'{material_data["month"]:02d}/{material_data["year"]}'

        date_group = [group for group in cost_list if group['date_str'] == date_str]
        if not date_group:
            date_group = {'date_str': date_str, 'values': []}
            cost_list.append(date_group)
        else:
            date_group = date_group[0]

        if material_data['codigo_projeto'] not in total_cost_dict:
            total_cost_dict[material_data['codigo_projeto']] = 0

        cost = total_cost_dict[material_data['codigo_projeto']] + float(material_data['cost'])
        total_cost_dict[material_data['codigo_projeto']] = cost

        date_group['values'].append({
            'codigo_projeto': material_data['codigo_projeto'],
            'nome_projeto': material_data['nome_projeto'],
            'cost': cost,
        })

    return cost_list


def get_resumo_projeto(projeto_id, data_inicio=None, data_fim=None):
    projeto = get_object_or_404(Projeto, id=projeto_id)
    custo_hora = projeto.custo_hora or Decimal('0')

    tempo_qs = TempoTarefa.objects.filter(tarefa__projeto_id=projeto_id)
    if data_inicio:
        tempo_qs = tempo_qs.filter(data__gte=data_inicio)
    if data_fim:
        tempo_qs = tempo_qs.filter(data__lte=data_fim)

    tempo_agg = tempo_qs.aggregate(
        horas=Sum('horas_trabalhadas'),
        custo=Sum(
            ExpressionWrapper(
                F('horas_trabalhadas') * custo_hora,
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
    )

    tempo_total = tempo_agg['horas'] or Decimal('0')
    custo_mao_de_obra = tempo_agg['custo'] or Decimal('0')

    materiais_qs = EmpenhoMaterial.objects.filter(projeto_id=projeto_id)
    if data_inicio:
        materiais_qs = materiais_qs.filter(data_empenho__gte=data_inicio)
    if data_fim:
        materiais_qs = materiais_qs.filter(data_empenho__lte=data_fim)

    custo_materiais = materiais_qs.aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantidade_empenhada') * F('material__custo_estimado'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
    )['total'] or Decimal('0')

    return {
        'custo_total': custo_mao_de_obra + custo_materiais,
        'tempo_total': tempo_total,
    }


def formatar_material(item):
    return {
        'nome_material': item['material__descricao'],
        'quantidade': item['quantidade'],
        'custo_total_estimado': float(item['custo_total_estimado'] or 0),
    }


def get_materiais_projeto(projeto_id, page=1, page_size=10, data_inicio=None, data_fim=None, material=None):
    page = normalizar_pagina(page)

    base_qs = EmpenhoMaterial.objects.filter(projeto_id=projeto_id)
    if data_inicio:
        base_qs = base_qs.filter(data_empenho__gte=data_inicio)
    if data_fim:
        base_qs = base_qs.filter(data_empenho__lte=data_fim)
    if material:
        base_qs = base_qs.filter(material__descricao__icontains=material)

    materiais_qs = (
        base_qs
        .values('material_id', 'material__descricao', 'material__custo_estimado')
        .annotate(quantidade=Sum('quantidade_empenhada'))
        .annotate(
            custo_total_estimado=ExpressionWrapper(
                F('quantidade') * F('material__custo_estimado'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
        .order_by('material__descricao')
    )

    total_items = materiais_qs.count()
    total_pages, start, end = calcular_paginacao(total_items, page, page_size)

    resultados = [formatar_material(item) for item in materiais_qs[start:end]]

    return {
        'count': total_items,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': resultados,
    }


def get_materiais_disponiveis(projeto_id):
    from ..models import Material
    return list(
        Material.objects
        .filter(empenhomaterial__projeto_id=projeto_id)
        .distinct()
        .order_by('descricao')
        .values('id', 'descricao')
    )
