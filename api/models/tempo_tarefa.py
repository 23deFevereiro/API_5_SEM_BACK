from django.db import models
from .tarefa_projeto import TarefaProjeto

class TempoTarefa(models.Model):
    usuario = models.CharField(max_length=50)
    data = models.DateField()
    horas_trabalhadas = models.DecimalField(max_digits=5, decimal_places=2)

    tarefa = models.ForeignKey(
        TarefaProjeto,
        on_delete=models.RESTRICT,
        related_name='tempos'
    )