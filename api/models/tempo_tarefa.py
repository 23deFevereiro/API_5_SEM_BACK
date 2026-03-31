from django.db import models
from .tarefa import Tarefa


class TempoTarefa(models.Model):
    tarefa = models.ForeignKey(Tarefa, on_delete=models.PROTECT, db_column='tarefa_id')
    usuario = models.CharField(max_length=255)
    data = models.DateField()
    horas_trabalhadas = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'tempo_tarefa'

    def __str__(self):
        return f'{self.tarefa} - {self.usuario} - {self.data}'
