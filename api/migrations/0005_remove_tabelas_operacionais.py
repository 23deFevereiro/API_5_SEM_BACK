from django.db import migrations


def drop_relational_tables(apps, schema_editor):
    tables = [
        'tempo_tarefa',
        'compras_projeto',
        'solicitacao_compra',
        'empenho_material',
        'estoque_material_projeto',
        'tarefa',
        'pedido_compra',
        'projeto',
        'material',
        'fornecedor',
        'programa',
        'demo',
    ]
    with schema_editor.connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')


def recreate_relational_tables(apps, schema_editor):
    model_names = [
        'Demo',
        'Fornecedor',
        'Material',
        'Programa',
        'PedidoCompra',
        'Projeto',
        'Tarefa',
        'EstoqueMaterialProjeto',
        'EmpenhoMaterial',
        'SolicitacaoCompra',
        'ComprasProjeto',
        'TempoTarefa',
    ]
    for model_name in model_names:
        model = apps.get_model('api', model_name)
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = %s)",
                [model._meta.db_table],
            )
            exists = cursor.fetchone()[0]
        if not exists:
            schema_editor.create_model(model)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_dimfornecedor_dimfuncionario_dimmaterial_dimprograma_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
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
            ],
            database_operations=[
                migrations.RunPython(
                    drop_relational_tables,
                    reverse_code=recreate_relational_tables,
                ),
            ],
        ),
    ]
