from django.db import models


class DimPrograma(models.Model):
    id = models.IntegerField(primary_key=True)
    codigo_programa = models.CharField(max_length=20, unique=True)
    nome_programa = models.CharField(max_length=100)
    gerente_programa = models.CharField(max_length=100, blank=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim_prevista = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, blank=True)

    class Meta:
        db_table = 'dim_programa'
