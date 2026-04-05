from math import ceil
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncWeek
from ..models import Projeto, Tarefa, TempoTarefa, EstoqueMaterialProjeto, ComprasProjeto, EmpenhoMaterial


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

def obter_dados_grafico_horas_acumuladas():

    dados_agrupados = (
        TempoTarefa.objects
        .annotate(semana=TruncWeek('data'))
        .values('tarefa__projeto__nome_projeto', 'semana')
        .annotate(total_horas=Sum('horas_trabalhadas'))
        .order_by('semana')
    )

    semanas_unicas = sorted(list(set(
        d['semana'].strftime('%Y-%m-%d') for d in dados_agrupados if d['semana']
    )))
    
    projetos_dict = {}

    for item in dados_agrupados:
        if not item['semana']:
            continue
            
        projeto_nome = item['tarefa__projeto__nome_projeto']
        semana_str = item['semana'].strftime('%Y-%m-%d')
        horas = float(item['total_horas'])

        if projeto_nome not in projetos_dict:
            projetos_dict[projeto_nome] = {s: 0.0 for s in semanas_unicas}
        
        projetos_dict[projeto_nome][semana_str] = horas

    projetos_data = []
    for projeto, dados_semana in projetos_dict.items():
        acumulado = 0
        data_points = []
        for semana in semanas_unicas:
            acumulado += dados_semana[semana]
            data_points.append(acumulado)
            
        projetos_data.append({
            "nome": projeto,
            "valores": data_points
        })

    labels_formatadas = [f"Semana {i+1}" for i in range(len(semanas_unicas))]

    return {
        "labels": labels_formatadas,
        "projetos": projetos_data
    }