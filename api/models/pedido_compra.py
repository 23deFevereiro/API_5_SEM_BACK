from django.db import models
from .fornecedor import Fornecedor

class PedidoCompra(models.Model):
    STATUS_CHOICES = [
        ('Aberto', 'Aberto'),
        ('Recebido', 'Recebido'),
        ('Parcialmente Recebido', 'Parcialmente Recebido'),
        ('Cancelado', 'Cancelado'),
    ]

    numero_pedido = models.CharField(max_length=20, unique=True)
    data_emissao = models.DateField()
    data_previsao_entrega = models.DateField()
    centro_custo = models.CharField(max_length=20)
    condicao_pagamento = models.CharField(max_length=30)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    prioridade = models.CharField(max_length=20)
    observacoes = models.CharField(max_length=255, blank=True, null=True)

    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.RESTRICT,
        related_name='pedidos'
    )