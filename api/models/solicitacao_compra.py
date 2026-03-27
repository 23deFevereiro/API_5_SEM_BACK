from django.db import models
from .projeto import Projeto
from .material import Material


class SolicitacaoCompra(models.Model):
    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Aprovada', 'Aprovada'),
        ('Rejeitada', 'Rejeitada'),
        ('Cancelada', 'Cancelada'),
    ]

    PRIORIDADE_CHOICES = [
        ('Alta', 'Alta'),
        ('Media', 'Media'),
        ('Baixa', 'Baixa'),
    ]

    numero_solicitacao = models.CharField(max_length=20, unique=True)
    projeto = models.ForeignKey(Projeto, on_delete=models.PROTECT, db_column='projeto_id')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, db_column='material_id')
    quantidade = models.IntegerField()
    data_solicitacao = models.DateField()
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'solicitacao_compra'

    def __str__(self):
        return f'{self.numero_solicitacao} - {self.status}'
