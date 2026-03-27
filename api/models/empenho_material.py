from django.db import models
from .projeto import Projeto
from .material import Material


class EmpenhoMaterial(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.PROTECT, db_column='projeto_id')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, db_column='material_id')
    quantidade_empenhada = models.IntegerField()
    data_empenho = models.DateField()

    class Meta:
        db_table = 'empenho_material'

    def __str__(self):
        return f'{self.projeto} - {self.material} - {self.quantidade_empenhada}'
