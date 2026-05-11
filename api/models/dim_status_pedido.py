from django.db import models


class DimStatusPedido(models.Model):
    nome_status = models.CharField(max_length=30, unique=True)
    categoria = models.CharField(max_length=20)
    ordem_prioridade = models.IntegerField(default=0)

    class Meta:
        db_table = "dim_status_pedido"
