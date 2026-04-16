from django.db import models
from .dim_programa import DimPrograma


class DimProjeto(models.Model):
    id = models.IntegerField(primary_key=True)
    codigo_projeto = models.CharField(max_length=20, unique=True)
    nome_projeto = models.CharField(max_length=100)
    programa = models.ForeignKey(DimPrograma, on_delete=models.CASCADE, null=True, blank=True)
    responsavel = models.CharField(max_length=100, null=True, blank=True)
    custo_hora = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = 'dim_projeto'
