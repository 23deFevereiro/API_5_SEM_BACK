from ..models import DimMaterial, FatoCompras, FatoEstoque, FatoMateriais
from datetime import date, timedelta
from django.db.models import F, IntegerField, Max, Min, OuterRef, Subquery, Sum
from django.db.models import ExpressionWrapper

PENDENTE_STATUS = ['Aberto', 'Enviado', 'Parcialmente Entregue']
DEFAULT_LEAD_TIME = 30
DIAS_COBERTURA_MAX = 60


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
