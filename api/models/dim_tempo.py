from django.db import models


class DimTempo(models.Model):
    id = models.IntegerField(primary_key=True)
    data = models.DateField(unique=True)
    ano = models.IntegerField()
    mes = models.IntegerField()
    trimestre = models.IntegerField()
    semestre = models.IntegerField()
    dia_semana = models.IntegerField()

    class Meta:
        db_table = 'dim_tempo'
