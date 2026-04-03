from django.db import models


class Material(models.Model):
    codigo_material = models.CharField(max_length=50, unique=True)
    descricao       = models.CharField(max_length=255)
    categoria       = models.CharField(max_length=100)
    fabricante      = models.CharField(max_length=255)
    custo_estimado  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status          = models.CharField(max_length=50)
    lead_time       = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = "api"
        db_table  = "materiais"

    def __str__(self):
        return self.codigo_material