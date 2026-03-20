from django.db import models

class ProgramaEmpresa(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Encerrado', 'Encerrado'),
        ('Planejamento', 'Planejamento'),
    ]

    codigo_programa = models.CharField(max_length=20)
    nome_programa = models.CharField(max_length=100)
    gerente_programa = models.CharField(max_length=100)
    data_inicio = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('codigo_programa', 'nome_programa')

    def __str__(self):
        return self.nome_programa