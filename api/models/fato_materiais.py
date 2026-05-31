from django.db import models

from .dim_fornecedor import DimFornecedor
from .dim_material import DimMaterial
from .dim_programa import DimPrograma
from .dim_projeto import DimProjeto
from .dim_tempo import DimTempo


class FatoMateriais(models.Model):
    tempo = models.ForeignKey(DimTempo, on_delete=models.CASCADE)
    projeto = models.ForeignKey(DimProjeto, on_delete=models.CASCADE)
    programa = models.ForeignKey(DimPrograma, on_delete=models.CASCADE)
    material = models.ForeignKey(DimMaterial, on_delete=models.CASCADE)
    fornecedor = models.ForeignKey(
        DimFornecedor, on_delete=models.CASCADE, null=True, blank=True
    )
    quantidade_empenhada = models.IntegerField(default=0)
    custo_materiais = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "fato_materiais"
        indexes = [
            models.Index(fields=["tempo"]),
            models.Index(fields=["material"]),
        ]
