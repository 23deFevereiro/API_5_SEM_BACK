from django.db import models
from .programa_empresa import ProgramaEmpresa

class ProjetoPrograma(models.Model):
    STATUS_CHOICES = [
        ('Em desenvolvimento', 'Em desenvolvimento'),
        ('Em testes', 'Em testes'),
        ('Concluído', 'Concluído'),
        ('Planejamento', 'Planejamento'),
    ]

    codigo_projeto = models.CharField(max_length=20)
    nome_projeto = models.CharField(max_length=100)
    responsavel = models.CharField(max_length=100)
    data_inicio = models.DateField()
    status = models.CharField(max_length=30)

    programa = models.ForeignKey(
        ProgramaEmpresa,
        on_delete=models.RESTRICT,
        related_name='projetos'
    )

    class Meta:
        unique_together = ('codigo_projeto', 'nome_projeto')

    def __str__(self):
        return self.nome_projeto