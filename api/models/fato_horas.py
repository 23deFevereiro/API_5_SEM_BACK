from django.db import models
from .dim_tempo import DimTempo
from .dim_projeto import DimProjeto
from .dim_programa import DimPrograma
from .dim_tarefa import DimTarefa
from .dim_funcionario import DimFuncionario


class FatoHoras(models.Model):
    tempo = models.ForeignKey(DimTempo, on_delete=models.CASCADE)
    projeto = models.ForeignKey(DimProjeto, on_delete=models.CASCADE)
    programa = models.ForeignKey(DimPrograma, on_delete=models.CASCADE)
    tarefa = models.ForeignKey(DimTarefa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(DimFuncionario, on_delete=models.CASCADE)
    horas_trabalhadas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    custo_horas = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'fato_horas'
        indexes = [
            models.Index(fields=['tempo']),
            models.Index(fields=['projeto']),
            models.Index(fields=['tarefa']),
        ]
