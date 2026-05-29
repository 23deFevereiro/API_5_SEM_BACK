from django.db import models


class DimFornecedor(models.Model):
    id = models.IntegerField(primary_key=True)
    codigo_fornecedor = models.CharField(max_length=20, unique=True)
    razao_social = models.CharField(max_length=120)
    cidade = models.CharField(max_length=50, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    categoria = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "dim_fornecedor"
