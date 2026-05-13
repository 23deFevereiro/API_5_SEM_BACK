from ..models import DimMaterial, FatoCompras, FatoMateriais


def listar_materiais_com_compras():
    ids_compras = set(FatoCompras.objects.values_list('material_id', flat=True).distinct())
    ids_materiais = set(FatoMateriais.objects.values_list('material_id', flat=True).distinct())
    ids = ids_compras | ids_materiais
    materiais = (
        DimMaterial.objects
        .filter(id__in=ids)
        .values('id', 'codigo_material', 'descricao')
        .order_by('descricao')
    )
    return list(materiais)


def get_lead_time_por_material(material_id):
    compras = (
        FatoCompras.objects
        .filter(material_id=material_id, lead_time__isnull=False)
        .select_related('fornecedor', 'status', 'tempo')
    )
    resultado = []
    vistos = set()
    for c in compras:
        chave = (c.fornecedor_id, c.tempo_id, c.status_id, c.lead_time, float(c.valor_total))
        if chave in vistos:
            continue
        vistos.add(chave)
        qtd = c.quantidade_solicitada if c.quantidade_solicitada else 1
        valor_unidade = round(float(c.valor_total) / qtd, 2)
        resultado.append({
            'fornecedor': c.fornecedor.razao_social,
            'lead_time': c.lead_time,
            'valor_unidade': valor_unidade,
            'valor_total': float(c.valor_total),
            'status': c.status.nome_status,
            'categoria_status': c.status.categoria,
            'data_pedido': str(c.tempo.data),
        })
    return resultado

def _get_consumo_diario_map():
    periodo = FatoMateriais.objects.aggregate(
        data_min=Min('tempo__data'),
        data_max=Max('tempo__data'),
    )

    if not periodo['data_min'] or not periodo['data_max']:
        return {}

    dias_periodo = max((periodo['data_max'] - periodo['data_min']).days + 1, 1)

    consumo_qs = (
        FatoMateriais.objects
        .values('material_id')
        .annotate(total_empenhado=Sum('quantidade_empenhada'))
    )

    return {
        item['material_id']: item['total_empenhado'] / dias_periodo
        for item in consumo_qs
        if item['total_empenhado'] and item['total_empenhado'] > 0
    }


def _get_estoque_atual_map():
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

    return {
        item['material_id']: item['estoque_total'] or 0
        for item in estoque_qs
    }


def _get_pedidos_pendentes_map():
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

    return {
        item['material_id']: max(item['qtd_pendente'] or 0, 0)
        for item in pendentes_qs
    }


def _get_menor_lead_time_map():
    compras = (
        FatoCompras.objects
        .filter(lead_time__isnull=False)
        .exclude(status__categoria='Cancelado')
        .select_related('fornecedor', 'material')
        .order_by('material_id', 'lead_time')
    )

    lead_time_map = {}

    for compra in compras:
        if compra.material_id not in lead_time_map:
            lead_time_map[compra.material_id] = {
                'lead_time': compra.lead_time,
                'fornecedor': compra.fornecedor.razao_social,
            }

    return lead_time_map


def get_sugestao_proxima_compra(data_referencia=None):
    data_referencia = data_referencia or date.today()

    consumo_map = _get_consumo_diario_map()
    if not consumo_map:
        return {
            'data_sugerida': None,
            'comprar_imediatamente': False,
            'materiais': [],
            'mensagem': 'Nenhum material precisa de compra no momento',
        }

    estoque_map = _get_estoque_atual_map()
    pendente_map = _get_pedidos_pendentes_map()
    lead_time_map = _get_menor_lead_time_map()

    nome_map = {
        material['id']: material['descricao']
        for material in DimMaterial.objects
        .filter(id__in=consumo_map.keys())
        .values('id', 'descricao')
    }

    materiais_recomendados = []

    for material_id, consumo_diario in consumo_map.items():
        if consumo_diario <= 0:
            continue

        estoque_atual = estoque_map.get(material_id, 0)
        pedidos_pendentes = pendente_map.get(material_id, 0)

        dias_cobertura = (estoque_atual + pedidos_pendentes) / consumo_diario

        if dias_cobertura >= DIAS_COBERTURA_MAX:
            continue

        lead_time_info = lead_time_map.get(material_id)
        lead_time = lead_time_info['lead_time'] if lead_time_info else DEFAULT_LEAD_TIME
        fornecedor = lead_time_info['fornecedor'] if lead_time_info else 'Fornecedor não definido'

        dias_ate_compra = round(dias_cobertura - lead_time)
        data_limite = data_referencia + timedelta(days=dias_ate_compra)

        materiais_recomendados.append({
            'material_id': material_id,
            'material': nome_map.get(material_id, str(material_id)),
            'fornecedor_sugerido': fornecedor,
            'dias_cobertura': round(dias_cobertura),
            'lead_time': lead_time,
            'data_limite_compra': data_limite.isoformat(),
            'comprar_imediatamente': data_limite <= data_referencia,
        })

    if not materiais_recomendados:
        return {
            'data_sugerida': None,
            'comprar_imediatamente': False,
            'materiais': [],
            'mensagem': 'Nenhum material precisa de compra no momento',
        }

    materiais_recomendados.sort(key=lambda item: item['data_limite_compra'])
    data_sugerida = materiais_recomendados[0]['data_limite_compra']
    comprar_imediatamente = materiais_recomendados[0]['comprar_imediatamente']

    return {
        'data_sugerida': data_sugerida,
        'comprar_imediatamente': comprar_imediatamente,
        'materiais': materiais_recomendados,
    }
