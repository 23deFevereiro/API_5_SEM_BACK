from datetime import date, timedelta
import math

from django.db.models import Avg, ExpressionWrapper, F, IntegerField, Max, Min, OuterRef, Subquery, Sum

from ..models import DimMaterial, FatoCompras, FatoEstoque, FatoMateriais

PENDENTE_STATUS = ['Aberto', 'Enviado', 'Parcialmente Entregue']
DIAS_COBERTURA_MAX = 60
STATUS_ENTREGUE = 'Entregue'


def _build_lead_time_map(lead_times_qs) -> dict[int, tuple[float, str]]:
    lead_time_map: dict[int, tuple[float, str]] = {}
    for lt in lead_times_qs:
        mid = lt['material_id']
        lt_medio = float(lt['lt_medio'])
        if mid not in lead_time_map or lt_medio < lead_time_map[mid][0]:
            lead_time_map[mid] = (lt_medio, lt['fornecedor__razao_social'])
    return lead_time_map


def _get_consumo_map(dias_periodo: int) -> dict[int, float]:
    consumo_qs = (
        FatoMateriais.objects
        .values('material_id')
        .annotate(total_empenhado=Sum('quantidade_empenhada'))
    )
    return {
        c['material_id']: c['total_empenhado'] / dias_periodo
        for c in consumo_qs
        if c['total_empenhado'] and c['total_empenhado'] > 0
    }


def _get_estoque_map() -> dict[int, int]:
    latest_date_subq = (
        FatoEstoque.objects
        .filter(material_id=OuterRef('material_id'))
        .values('material_id')
        .annotate(max_date=Max('tempo__data'))
        .values('max_date')[:1]
    )
    estoque_qs = (
        FatoEstoque.objects
        .annotate(latest_date=Subquery(latest_date_subq))
        .filter(tempo__data=F('latest_date'))
        .values('material_id')
        .annotate(estoque_total=Sum('quantidade_estoque'))
    )
    return {e['material_id']: e['estoque_total'] or 0 for e in estoque_qs}


def _get_pendente_map() -> dict[int, int]:
    pendentes_qs = (
        FatoCompras.objects
        .filter(status__nome_status__in=PENDENTE_STATUS)
        .values('material_id')
        .annotate(
            qtd_pendente=Sum(
                ExpressionWrapper(
                    F('quantidade_solicitada') - F('quantidade_entregue'),
                    output_field=IntegerField(),
                )
            )
        )
    )
    return {p['material_id']: max(p['qtd_pendente'] or 0, 0) for p in pendentes_qs}


def _classify_material(mat_id, consumo_diario, estoque_map, pendente_map, lead_time_map, nome_map):
    estoque = estoque_map.get(mat_id, 0)
    pendente = pendente_map.get(mat_id, 0)
    dias_cobertura = max(estoque + pendente, 0) / consumo_diario

    if mat_id in lead_time_map:
        lt_min, fornecedor_nome = lead_time_map[mat_id]
        dias_para_pedir = dias_cobertura - lt_min
    else:
        lt_min = 0.0
        fornecedor_nome = '-'
        dias_para_pedir = dias_cobertura

    return dias_para_pedir, {
        'material': nome_map.get(mat_id, str(mat_id)),
        'dias_para_pedir': round(dias_para_pedir),
        'lead_time_min': round(lt_min),
        'fornecedor': fornecedor_nome,
        'dias_cobertura': round(dias_cobertura),
    }


def get_alertas_materiais(critico_max: int = 30, atencao_max: int = 60):
    tempo_range = FatoMateriais.objects.aggregate(
        data_min=Min('tempo__data'),
        data_max=Max('tempo__data'),
    )
    if not tempo_range['data_min'] or not tempo_range['data_max']:
        return {'criticos': [], 'atencao': []}

    dias_periodo = max((tempo_range['data_max'] - tempo_range['data_min']).days + 1, 1)

    consumo_map = _get_consumo_map(dias_periodo)
    if not consumo_map:
        return {'criticos': [], 'atencao': []}

    estoque_map = _get_estoque_map()
    pendente_map = _get_pendente_map()
    lead_time_map = _build_lead_time_map(
        FatoCompras.objects
        .filter(lead_time__isnull=False)
        .exclude(status__categoria='Cancelado')
        .values('material_id', 'fornecedor_id', 'fornecedor__razao_social')
        .annotate(lt_medio=Avg('lead_time'))
    )
    nome_map = {
        m['id']: m['descricao']
        for m in DimMaterial.objects.filter(id__in=consumo_map.keys()).values('id', 'descricao')
    }

    criticos, atencao = [], []
    for mat_id, consumo_diario in consumo_map.items():
        dias_para_pedir, item = _classify_material(
            mat_id, consumo_diario, estoque_map, pendente_map, lead_time_map, nome_map
        )
        if dias_para_pedir <= critico_max:
            criticos.append(item)
        elif dias_para_pedir <= atencao_max:
            atencao.append(item)

    criticos.sort(key=lambda x: x['dias_para_pedir'])
    atencao.sort(key=lambda x: x['dias_para_pedir'])

    return {'criticos': criticos, 'atencao': atencao[:5]}


_VALID_SORT_KEYS = {'material', 'projeto', 'dias_ate_acabar', 'status'}
_STATUS_ORDER = {'Urgente': 0, 'Atenção': 1, 'Ok': 2}


def _classify_status(dias_para_pedir: float, critico_max: int, atencao_max: int) -> str:
    if dias_para_pedir <= critico_max:
        return 'Urgente'
    if dias_para_pedir <= atencao_max:
        return 'Atenção'
    return 'Ok'


def _build_estoque_row(mat_id, consumo_diario, estoque_map, lead_time_map, nome_map, projeto_map, critico_max, atencao_max):
    estoque = estoque_map.get(mat_id, 0)
    dias_cobertura = estoque / consumo_diario

    if mat_id in lead_time_map:
        lt_min, _ = lead_time_map[mat_id]
        status = _classify_status(dias_cobertura - lt_min, critico_max, atencao_max)
    else:
        status = _classify_status(dias_cobertura, critico_max, atencao_max)

    return {
        'material': nome_map.get(mat_id, str(mat_id)),
        'projeto': projeto_map.get(mat_id, ''),
        'estoque_atual': estoque,
        'consumo_previsto': round(consumo_diario, 2),
        'dias_ate_acabar': round(dias_cobertura),
        'status': status,
    }


def _sort_estoque_results(results: list, sort_by: str, sort_dir: str) -> None:
    effective_sort = sort_by if sort_by in _VALID_SORT_KEYS else 'status'
    reverse = sort_dir == 'desc'
    sort_keys = {
        'status': lambda x: (_STATUS_ORDER[x['status']], x['material']),
        'material': lambda x: x['material'].lower(),
        'projeto': lambda x: x['projeto'].lower(),
        'dias_ate_acabar': lambda x: x['dias_ate_acabar'],
    }
    results.sort(key=sort_keys[effective_sort], reverse=reverse)


def get_estoque_tabela(critico_max: int = 30, atencao_max: int = 60, page: int = 1, page_size: int = 5, material_id: int | None = None, sort_by: str = 'status', sort_dir: str = 'asc'):
    vazio = {'count': 0, 'page': page, 'page_size': page_size, 'total_pages': 0, 'results': []}

    tempo_range = FatoMateriais.objects.aggregate(
        data_min=Min('tempo__data'),
        data_max=Max('tempo__data'),
    )
    if not tempo_range['data_min'] or not tempo_range['data_max']:
        return vazio

    dias_periodo = max((tempo_range['data_max'] - tempo_range['data_min']).days + 1, 1)
    consumo_map = _get_consumo_map(dias_periodo)
    if material_id is not None:
        consumo_map = {k: v for k, v in consumo_map.items() if k == material_id}
    if not consumo_map:
        return vazio

    estoque_map = _get_estoque_map()
    lead_time_map = _build_lead_time_map(
        FatoCompras.objects
        .filter(lead_time__isnull=False)
        .exclude(status__categoria='Cancelado')
        .values('material_id', 'fornecedor_id', 'fornecedor__razao_social')
        .annotate(lt_medio=Avg('lead_time'))
    )
    nome_map = {
        m['id']: m['descricao']
        for m in DimMaterial.objects.filter(id__in=consumo_map.keys()).values('id', 'descricao')
    }

    projeto_qs = (
        FatoMateriais.objects
        .filter(material_id__in=consumo_map.keys())
        .values('material_id', 'projeto__nome_projeto')
        .annotate(total=Sum('quantidade_empenhada'))
        .order_by('material_id', '-total')
    )
    projeto_map: dict[int, str] = {}
    for p in projeto_qs:
        mid = p['material_id']
        if mid not in projeto_map:
            projeto_map[mid] = p['projeto__nome_projeto'] or ''

    results = [
        _build_estoque_row(mat_id, consumo_diario, estoque_map, lead_time_map, nome_map, projeto_map, critico_max, atencao_max)
        for mat_id, consumo_diario in consumo_map.items()
    ]

    _sort_estoque_results(results, sort_by, sort_dir)

    total = len(results)
    total_pages = max(1, math.ceil(total / page_size))
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size

    return {
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': results[start:start + page_size],
    }

MENSAGEM_NENHUM_MATERIAL = 'Nenhum material precisa de compra no momento'


def _empty_sugestao_proxima_compra():
    return {
        'data_sugerida': None,
        'comprar_imediatamente': False,
        'materiais': [],
        'mensagem': MENSAGEM_NENHUM_MATERIAL,
    }


def get_sugestao_proxima_compra(data_referencia=None):
    data_referencia = data_referencia or date.today()

    tempo_range = FatoMateriais.objects.aggregate(
        data_min=Min('tempo__data'),
        data_max=Max('tempo__data'),
    )

    if not tempo_range['data_min'] or not tempo_range['data_max']:
        return _empty_sugestao_proxima_compra()

    dias_periodo = max((tempo_range['data_max'] - tempo_range['data_min']).days + 1, 1)

    consumo_map = _get_consumo_map(dias_periodo)
    if not consumo_map:
        return _empty_sugestao_proxima_compra()

    estoque_map = _get_estoque_map()
    pendente_map = _get_pendente_map()

    lead_time_map = _build_lead_time_map(
        FatoCompras.objects
        .filter(
            lead_time__isnull=False,
            status__nome_status=STATUS_ENTREGUE,
        )
        .values('material_id', 'fornecedor_id', 'fornecedor__razao_social')
        .annotate(lt_medio=Min('lead_time'))
    )

    nome_map = {
        m['id']: m['descricao']
        for m in DimMaterial.objects
        .filter(id__in=consumo_map.keys())
        .values('id', 'descricao')
    }

    materiais = []

    for mat_id, consumo_diario in consumo_map.items():
        if consumo_diario <= 0:
            continue

        estoque = estoque_map.get(mat_id, 0)
        pendente = pendente_map.get(mat_id, 0)
        dias_cobertura = (estoque + pendente) / consumo_diario

        if dias_cobertura >= DIAS_COBERTURA_MAX:
            continue

        if mat_id in lead_time_map:
            lead_time, fornecedor = lead_time_map[mat_id]
        else:
            lead_time = 30
            fornecedor = 'Fornecedor não definido'

        dias_para_pedir = dias_cobertura - lead_time
        data_limite_compra = data_referencia + timedelta(days=round(dias_para_pedir))

        materiais.append({
            'material_id': mat_id,
            'material': nome_map.get(mat_id, str(mat_id)),
            'fornecedor_sugerido': fornecedor,
            'dias_cobertura': round(dias_cobertura),
            'lead_time': round(lead_time),
            'dias_para_pedir': round(dias_para_pedir),
            'data_limite_compra': data_limite_compra.isoformat(),
            'comprar_imediatamente': data_limite_compra <= data_referencia,
        })

    if not materiais:
        return _empty_sugestao_proxima_compra()

    materiais.sort(key=lambda item: item['data_limite_compra'])

    return {
        'data_sugerida': materiais[0]['data_limite_compra'],
        'comprar_imediatamente': materiais[0]['comprar_imediatamente'],
        'materiais': materiais,
    }
