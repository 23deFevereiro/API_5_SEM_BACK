from django.db import models


class DimMaterial(models.Model):
    id = models.IntegerField(primary_key=True)
    codigo_material = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=200)
    categoria = models.CharField(max_length=50, blank=True)
    fabricante = models.CharField(max_length=100, blank=True)
    custo_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'dim_material'
