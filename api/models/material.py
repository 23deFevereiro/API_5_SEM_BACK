from django.db import models


class Material(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
        ('Obsoleto', 'Obsoleto'),
    ]

    codigo_material = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=255)
    categoria = models.CharField(max_length=100)
    fabricante = models.CharField(max_length=100)
    custo_estimado = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'material'

    def __str__(self):
        return f'{self.codigo_material} - {self.descricao}'
