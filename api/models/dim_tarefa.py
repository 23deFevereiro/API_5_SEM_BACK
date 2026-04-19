from django.db import models
from .dim_projeto import DimProjeto


class DimTarefa(models.Model):
    id = models.IntegerField(primary_key=True)
    codigo_tarefa = models.CharField(max_length=20, unique=True)
    projeto = models.ForeignKey(DimProjeto, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    responsavel = models.CharField(max_length=100, blank=True)
    horas_estimadas = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=30, blank=True)

    class Meta:
        db_table = 'dim_tarefa'
