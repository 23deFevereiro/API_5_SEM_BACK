from django.core.management.base import BaseCommand

from api.management.commands.seeds.seed_0005 import _none
from api.management.commands.seeds.seed_0005 import run as _run_base

MIGRATION_REF = "0006"


def carregar_dim_projeto(df, cursor):
    cursor.execute("TRUNCATE TABLE dim_projeto RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO dim_projeto (id, codigo_projeto, nome_projeto, programa_id, responsavel,
                                     custo_hora, status, data_inicio, data_fim_prevista)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                codigo_projeto = EXCLUDED.codigo_projeto,
                nome_projeto = EXCLUDED.nome_projeto,
                programa_id = EXCLUDED.programa_id,
                responsavel = EXCLUDED.responsavel,
                custo_hora = EXCLUDED.custo_hora,
                status = EXCLUDED.status,
                data_inicio = EXCLUDED.data_inicio,
                data_fim_prevista = EXCLUDED.data_fim_prevista
        """,
            (
                row["id"],
                row["codigo_projeto"],
                row["nome_projeto"],
                row["programa_id"],
                row["responsavel"],
                row["custo_hora"],
                row["status"],
                _none(row["data_inicio"]),
                _none(row["data_fim_prevista"]),
            ),
        )
    print(f"   ✅ dim_projeto: {len(df)} registros")


def run():
    print(
        f"\n📦 Seed {MIGRATION_REF} - Carregando dimensões e fatos do Star Model (com data_inicio/data_fim_prevista em dim_projeto)..."
    )
    _run_base(carregar_projeto_fn=carregar_dim_projeto)


class Command(BaseCommand):
    help = f"Seed {MIGRATION_REF}: popula as tabelas do Star Model com data_inicio e data_fim_prevista em dim_projeto"

    def handle(self, *args, **options):
        run()
