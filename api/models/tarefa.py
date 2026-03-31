from django.db import models
from .projeto import Projeto


class Tarefa(models.Model):
    STATUS_CHOICES = [
        ('Nao iniciada', 'Nao iniciada'),
        ('Em andamento', 'Em andamento'),
        ('Concluida', 'Concluida'),
        ('Bloqueada', 'Bloqueada'),
    ]

    codigo_tarefa = models.CharField(max_length=20, unique=True)
    projeto = models.ForeignKey(Projeto, on_delete=models.PROTECT, db_column='projeto_id')
    titulo = models.CharField(max_length=255)
    responsavel = models.CharField(max_length=255)
    estimativa_horas = models.DecimalField(max_digits=10, decimal_places=2)
    data_inicio = models.DateField()
    data_fim_prevista = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'tarefa'

    def __str__(self):
        return f'{self.codigo_tarefa} - {self.titulo}'
