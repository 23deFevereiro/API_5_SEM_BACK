from django.db import models


class Programa(models.Model):
    STATUS_CHOICES = [
        ('Em andamento', 'Em andamento'),
        ('Concluido', 'Concluido'),
    ]

    codigo_programa = models.CharField(max_length=20, unique=True)
    nome_programa = models.CharField(max_length=255)
    gerente_programa = models.CharField(max_length=255)
    gerente_tecnico = models.CharField(max_length=255)
    data_inicio = models.DateField()
    data_fim_prevista = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'programa'

    def __str__(self):
        return f'{self.codigo_programa} - {self.nome_programa}'
