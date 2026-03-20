from django.db import models
from .projeto_programa import ProjetoPrograma

class TarefaProjeto(models.Model):
    STATUS_CHOICES = [
        ('Concluída', 'Concluída'),
        ('Em andamento', 'Em andamento'),
        ('Backlog', 'Backlog'),
    ]

    codigo_tarefa = models.CharField(max_length=20, unique=True)
    titulo = models.CharField(max_length=150)
    responsavel = models.CharField(max_length=100)
    estimativa_horas = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    projeto = models.ForeignKey(
        ProjetoPrograma,
        on_delete=models.RESTRICT,
        related_name='tarefas'
    )