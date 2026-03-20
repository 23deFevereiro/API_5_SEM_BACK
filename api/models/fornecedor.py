from django.db import models


class Fornecedor(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
        ('Bloqueado', 'Bloqueado'),
    ]

    codigo_fornecedor = models.CharField(max_length=20, unique=True)
    razao_social = models.CharField(max_length=255)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    categoria = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'fornecedor'

    def __str__(self):
        return f'{self.codigo_fornecedor} - {self.razao_social}'
