from django.db import models
from .projeto_programa import ProjetoPrograma
from .pedido_compra import PedidoCompra

class CompraProjeto(models.Model):
    valor_alocado = models.DecimalField(max_digits=12, decimal_places=2)

    projeto = models.ForeignKey(ProjetoPrograma, on_delete=models.RESTRICT)
    pedido = models.ForeignKey(PedidoCompra, on_delete=models.RESTRICT)