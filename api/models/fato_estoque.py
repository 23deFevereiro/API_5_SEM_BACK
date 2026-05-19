from django.db import models
from .dim_tempo import DimTempo
from .dim_material import DimMaterial
from .dim_projeto import DimProjeto


class FatoEstoque(models.Model):
    tempo = models.ForeignKey(DimTempo, on_delete=models.CASCADE)
    material = models.ForeignKey(DimMaterial, on_delete=models.CASCADE)
    projeto = models.ForeignKey(DimProjeto, on_delete=models.CASCADE)
    quantidade_estoque = models.IntegerField(default=0)

    class Meta:
        db_table = 'fato_estoque'
        indexes = [
            models.Index(fields=['material']),
        ]
