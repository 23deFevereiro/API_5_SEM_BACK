from django.db import models
from .projeto import Projeto
from .pedido_compra import PedidoCompra


class ComprasProjeto(models.Model):
    pedido_compra = models.ForeignKey(PedidoCompra, on_delete=models.PROTECT, db_column='pedido_compra_id')
    projeto = models.ForeignKey(Projeto, on_delete=models.PROTECT, db_column='projeto_id')
    valor_alocado = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'compras_projeto'

    def __str__(self):
        return f'{self.projeto} - {self.pedido_compra} - {self.valor_alocado}'
