from django.db import models
from .dim_tempo import DimTempo
from .dim_projeto import DimProjeto
from .dim_material import DimMaterial
from .dim_fornecedor import DimFornecedor
from .dim_status_pedido import DimStatusPedido


class FatoCompras(models.Model):
    tempo = models.ForeignKey(DimTempo, on_delete=models.CASCADE)
    projeto = models.ForeignKey(DimProjeto, on_delete=models.CASCADE, null=True, blank=True)
    material = models.ForeignKey(DimMaterial, on_delete=models.CASCADE)
    fornecedor = models.ForeignKey(DimFornecedor, on_delete=models.CASCADE)
    status = models.ForeignKey(DimStatusPedido, on_delete=models.CASCADE)
    quantidade_solicitada = models.IntegerField(default=0)
    quantidade_entregue = models.IntegerField(default=0)
    valor_alocado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lead_time = models.IntegerField(null=True, blank=True)
    data_previsao_entrega = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'fato_compras'
        indexes = [
            models.Index(fields=['tempo']),
            models.Index(fields=['material']),
        ]
