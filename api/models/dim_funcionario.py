from django.db import models


class DimFuncionario(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'dim_funcionario'
