from django.db import models
from .projeto import Projeto
from .material import Material


class EstoqueMaterialProjeto(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.PROTECT, db_column='projeto_id')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, db_column='material_id')
    quantidade = models.IntegerField()
    localizacao = models.CharField(max_length=100)

    class Meta:
        db_table = 'estoque_material_projeto'

    def __str__(self):
        return f'{self.projeto} - {self.material} - {self.quantidade}'
