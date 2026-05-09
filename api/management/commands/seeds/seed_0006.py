import pandas as pd
from django.core.management.base import BaseCommand
from api.management.commands.seeds.seed_0005 import (
    get_connection,
    _none,
    carregar_dim_programa,
    carregar_dim_tarefa,
    carregar_dim_material,
    carregar_dim_fornecedor,
    carregar_dim_funcionario,
    carregar_dim_status_pedido,
    carregar_dim_tempo,
    carregar_fato_horas,
    carregar_fato_materiais,
    carregar_fato_compras,
    carregar_fato_estoque,
    CSV_DIR,
)

MIGRATION_REF = '0006'


def carregar_dim_projeto(df, cursor):
    cursor.execute("TRUNCATE TABLE dim_projeto RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
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
        """, (
            row['id'], row['codigo_projeto'], row['nome_projeto'],
            row['programa_id'], row['responsavel'], row['custo_hora'], row['status'],
            _none(row['data_inicio']), _none(row['data_fim_prevista'])
        ))
    print(f"   ✅ dim_projeto: {len(df)} registros")


def run():
    print(f"\n📦 Seed {MIGRATION_REF} - Carregando dimensões e fatos do Star Model (com data_inicio/data_fim_prevista em dim_projeto)...")

    print("\n   📖 Lendo CSVs...")
    df_programas = pd.read_csv(CSV_DIR / 'programas.csv')
    df_projetos = pd.read_csv(CSV_DIR / 'projetos_corrigido.csv')
    df_tarefas = pd.read_csv(CSV_DIR / 'tarefas_projeto_corrigido.csv')
    df_materiais = pd.read_csv(CSV_DIR / 'materiais.csv')
    df_fornecedores = pd.read_csv(CSV_DIR / 'fornecedores.csv')
    df_tempo_tarefas = pd.read_csv(CSV_DIR / 'tempo_tarefas_corrigido.csv')
    df_empenho = pd.read_csv(CSV_DIR / 'empenho_materiais_corrigido.csv')
    df_solicitacoes = pd.read_csv(CSV_DIR / 'solicitacoes_compra_corrigido.csv')
    df_pedidos = pd.read_csv(CSV_DIR / 'pedidos_compra_corrigido.csv')
    df_compras_projeto = pd.read_csv(CSV_DIR / 'compras_projeto.csv')
    df_estoque = pd.read_csv(CSV_DIR / 'estoque_materiais_projeto.csv')
    print("   ✅ CSVs carregados")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("\n   📥 Carregando dimensões...")
        carregar_dim_programa(df_programas, cursor)
        carregar_dim_projeto(df_projetos, cursor)
        carregar_dim_tarefa(df_tarefas, cursor)
        carregar_dim_material(df_materiais, cursor)
        carregar_dim_fornecedor(df_fornecedores, cursor)
        carregar_dim_funcionario(df_tempo_tarefas, cursor)
        carregar_dim_status_pedido(cursor)
        carregar_dim_tempo(cursor)

        cursor.execute("SELECT id, nome FROM dim_funcionario")
        df_funcionario = pd.DataFrame(cursor.fetchall(), columns=['id', 'nome'])

        print("\n   📊 Carregando fatos...")
        carregar_fato_horas(df_tempo_tarefas, df_tarefas, df_projetos, df_programas, df_funcionario, cursor)
        carregar_fato_materiais(df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, df_solicitacoes, df_pedidos, cursor)

        cursor.execute("SELECT id, nome_status FROM dim_status_pedido")
        df_status_pedido = pd.DataFrame(cursor.fetchall(), columns=['id', 'nome_status'])

        carregar_fato_compras(df_solicitacoes, df_pedidos, df_compras_projeto, df_projetos,
                              df_materiais, df_fornecedores, df_status_pedido, cursor)
        carregar_fato_estoque(df_estoque, cursor)

        conn.commit()
        print(f"\n   ✅ Seed {MIGRATION_REF} concluído com sucesso!")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


class Command(BaseCommand):
    help = f'Seed {MIGRATION_REF}: popula as tabelas do Star Model com data_inicio e data_fim_prevista em dim_projeto'

    def handle(self, *args, **options):
        run()
