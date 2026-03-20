from django.db import models
from .programa import Programa


class Projeto(models.Model):
    STATUS_CHOICES = [
        ('Planejamento', 'Planejamento'),
        ('Em andamento', 'Em andamento'),
        ('Concluido', 'Concluido'),
        ('Suspenso', 'Suspenso'),
    ]

    codigo_projeto = models.CharField(max_length=20, unique=True)
    nome_projeto = models.CharField(max_length=255)
    programa = models.ForeignKey(Programa, on_delete=models.PROTECT, db_column='programa_id')
    responsavel = models.CharField(max_length=255)
    custo_hora = models.DecimalField(max_digits=10, decimal_places=2)
    data_inicio = models.DateField()
    data_fim_prevista = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'projeto'

    def __str__(self):
        return f'{self.codigo_projeto} - {self.nome_projeto}'
