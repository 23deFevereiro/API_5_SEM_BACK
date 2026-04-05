from django.db import models
from .fornecedor import Fornecedor


class PedidoCompra(models.Model):
    STATUS_CHOICES = [
        ('Aberto', 'Aberto'),
        ('Entregue', 'Entregue'),
        ('Parcialmente Entregue', 'Parcialmente Entregue'),
        ('Cancelado', 'Cancelado'),
    ]

    numero_pedido = models.CharField(max_length=20, unique=True)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, db_column='fornecedor_id')
    data_pedido = models.DateField()
    data_previsao_entrega = models.DateField()
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'pedido_compra'

    def __str__(self):
        return f'{self.numero_pedido} - {self.status}'
