from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_remove_tabelas_operacionais"),
    ]

    operations = [
        migrations.AddField(
            model_name="dimprojeto",
            name="data_inicio",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dimprojeto",
            name="data_fim_prevista",
            field=models.DateField(blank=True, null=True),
        ),
    ]
