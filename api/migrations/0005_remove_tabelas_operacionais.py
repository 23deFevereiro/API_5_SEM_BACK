from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_dimfornecedor_dimfuncionario_dimmaterial_dimprograma_and_more'),
    ]

    operations = [
        migrations.DeleteModel(name='ComprasProjeto'),
        migrations.DeleteModel(name='SolicitacaoCompra'),
        migrations.DeleteModel(name='PedidoCompra'),
        migrations.DeleteModel(name='EmpenhoMaterial'),
        migrations.DeleteModel(name='EstoqueMaterialProjeto'),
        migrations.DeleteModel(name='TempoTarefa'),
        migrations.DeleteModel(name='Tarefa'),
        migrations.DeleteModel(name='Projeto'),
        migrations.DeleteModel(name='Material'),
        migrations.DeleteModel(name='Fornecedor'),
        migrations.DeleteModel(name='Programa'),
        migrations.DeleteModel(name='Demo'),
    ]
