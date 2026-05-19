import pandas as pd
import psycopg2
import os
from pathlib import Path
from django.core.management.base import BaseCommand


DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'database'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}

MIGRATION_REF = '0003'
CSV_DIR = Path(__file__).parent.parent / 'corrected_documents'


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def _none(val):
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(val, 'item'):
        return val.item()
    return val


def carregar_programa(df, cursor):
    cursor.execute("TRUNCATE TABLE programa RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO programa (id, codigo_programa, nome_programa, gerente_programa,
                                  gerente_tecnico, data_inicio, data_fim_prevista, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                codigo_programa = EXCLUDED.codigo_programa,
                nome_programa = EXCLUDED.nome_programa,
                gerente_programa = EXCLUDED.gerente_programa,
                gerente_tecnico = EXCLUDED.gerente_tecnico,
                data_inicio = EXCLUDED.data_inicio,
                data_fim_prevista = EXCLUDED.data_fim_prevista,
                status = EXCLUDED.status
        """, (
            _none(row['id']), row['codigo_programa'], row['nome_programa'],
            _none(row.get('gerente_programa')), _none(row.get('gerente_tecnico', '')),
            row['data_inicio'], _none(row['data_fim_prevista']), row['status']
        ))
    print(f"   ✅ programa: {len(df)} registros")


def carregar_projeto(df, cursor):
    cursor.execute("TRUNCATE TABLE projeto RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO projeto (id, codigo_projeto, nome_projeto, programa_id, responsavel,
                                 custo_hora, data_inicio, data_fim_prevista, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                codigo_projeto = EXCLUDED.codigo_projeto,
                nome_projeto = EXCLUDED.nome_projeto,
                programa_id = EXCLUDED.programa_id,
                responsavel = EXCLUDED.responsavel,
                custo_hora = EXCLUDED.custo_hora,
                data_inicio = EXCLUDED.data_inicio,
                data_fim_prevista = EXCLUDED.data_fim_prevista,
                status = EXCLUDED.status
        """, (
            _none(row['id']), row['codigo_projeto'], row['nome_projeto'],
            _none(row['programa_id']), row['responsavel'], _none(row['custo_hora']),
            row['data_inicio'], _none(row['data_fim_prevista']), row['status']
        ))
    print(f"   ✅ projeto: {len(df)} registros")


def carregar_tarefa(df, cursor):
    cursor.execute("TRUNCATE TABLE tarefa RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO tarefa (id, codigo_tarefa, projeto_id, titulo, responsavel,
                                estimativa_horas, data_inicio, data_fim_prevista, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                codigo_tarefa = EXCLUDED.codigo_tarefa,
                projeto_id = EXCLUDED.projeto_id,
                titulo = EXCLUDED.titulo,
                responsavel = EXCLUDED.responsavel,
                estimativa_horas = EXCLUDED.estimativa_horas,
                data_inicio = EXCLUDED.data_inicio,
                data_fim_prevista = EXCLUDED.data_fim_prevista,
                status = EXCLUDED.status
        """, (
            _none(row['id']), row['codigo_tarefa'], _none(row['projeto_id']), row['titulo'],
            row['responsavel'], _none(row.get('estimativa_horas')),
            row['data_inicio'], _none(row['data_fim_prevista']), row['status']
        ))
    print(f"   ✅ tarefa: {len(df)} registros")


def carregar_tempo_tarefa(df, cursor):
    cursor.execute("TRUNCATE TABLE tempo_tarefa RESTART IDENTITY CASCADE;")
    registros = 0
    for _, row in df.iterrows():
        horas = _none(row['horas_trabalhadas'])
        if horas is None:
            continue
        cursor.execute("""
            INSERT INTO tempo_tarefa (tarefa_id, usuario, data, horas_trabalhadas)
            VALUES (%s, %s, %s, %s)
        """, (int(row['tarefa_id']), row['usuario'], row['data'], float(horas)))
        registros += 1
    print(f"   ✅ tempo_tarefa: {registros} registros")


def carregar_fornecedor(df, cursor):
    cursor.execute("TRUNCATE TABLE fornecedor RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO fornecedor (id, codigo_fornecedor, razao_social, cidade,
                                    estado, categoria, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                codigo_fornecedor = EXCLUDED.codigo_fornecedor,
                razao_social = EXCLUDED.razao_social,
                cidade = EXCLUDED.cidade,
                estado = EXCLUDED.estado,
                categoria = EXCLUDED.categoria,
                status = EXCLUDED.status
        """, (
            _none(row['id']), row['codigo_fornecedor'], row['razao_social'],
            row['cidade'], row['estado'], row['categoria'], row['status']
        ))
    print(f"   ✅ fornecedor: {len(df)} registros")


def carregar_material(df, cursor):
    cursor.execute("TRUNCATE TABLE material RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO material (id, codigo_material, descricao, categoria,
                                  fabricante, custo_estimado, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                codigo_material = EXCLUDED.codigo_material,
                descricao = EXCLUDED.descricao,
                categoria = EXCLUDED.categoria,
                fabricante = EXCLUDED.fabricante,
                custo_estimado = EXCLUDED.custo_estimado,
                status = EXCLUDED.status
        """, (
            _none(row['id']), row['codigo_material'], row['descricao'],
            row['categoria'], row['fabricante'], _none(row['custo_estimado']), row['status']
        ))
    print(f"   ✅ material: {len(df)} registros")


def carregar_pedido_compra(df, cursor):
    cursor.execute("TRUNCATE TABLE pedido_compra RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO pedido_compra (id, numero_pedido, fornecedor_id, data_pedido,
                                       data_previsao_entrega, valor_total, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                numero_pedido = EXCLUDED.numero_pedido,
                fornecedor_id = EXCLUDED.fornecedor_id,
                data_pedido = EXCLUDED.data_pedido,
                data_previsao_entrega = EXCLUDED.data_previsao_entrega,
                valor_total = EXCLUDED.valor_total,
                status = EXCLUDED.status
        """, (
            _none(row['id']), row['numero_pedido'], int(row['fornecedor_id']),
            row['data_pedido'], _none(row['data_previsao_entrega']),
            _none(row['valor_total']), row['status']
        ))
    print(f"   ✅ pedido_compra: {len(df)} registros")


def carregar_compras_projeto(df, cursor):
    cursor.execute("TRUNCATE TABLE compras_projeto RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO compras_projeto (id, pedido_compra_id, projeto_id, valor_alocado)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                pedido_compra_id = EXCLUDED.pedido_compra_id,
                projeto_id = EXCLUDED.projeto_id,
                valor_alocado = EXCLUDED.valor_alocado
        """, (
            int(row['id']), int(row['pedido_compra_id']),
            int(row['projeto_id']), float(row['valor_alocado'])
        ))
    print(f"   ✅ compras_projeto: {len(df)} registros")


def carregar_solicitacao_compra(df, cursor):
    cursor.execute("TRUNCATE TABLE solicitacao_compra RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO solicitacao_compra (id, numero_solicitacao, projeto_id, material_id,
                                            quantidade, data_solicitacao, prioridade, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                numero_solicitacao = EXCLUDED.numero_solicitacao,
                projeto_id = EXCLUDED.projeto_id,
                material_id = EXCLUDED.material_id,
                quantidade = EXCLUDED.quantidade,
                data_solicitacao = EXCLUDED.data_solicitacao,
                prioridade = EXCLUDED.prioridade,
                status = EXCLUDED.status
        """, (
            row['id'], row['numero_solicitacao'], int(row['projeto_id']),
            int(row['material_id']), int(row['quantidade']),
            row['data_solicitacao'], row['prioridade'], row['status']
        ))
    print(f"   ✅ solicitacao_compra: {len(df)} registros")


def carregar_empenho_material(df, cursor):
    cursor.execute("TRUNCATE TABLE empenho_material RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO empenho_material (projeto_id, material_id, quantidade_empenhada, data_empenho)
            VALUES (%s, %s, %s, %s)
        """, (
            int(row['projeto_id']), int(row['material_id']),
            int(row['quantidade_empenhada']), row['data_empenho']
        ))
    print(f"   ✅ empenho_material: {len(df)} registros")


def carregar_estoque_material_projeto(df, cursor):
    cursor.execute("TRUNCATE TABLE estoque_material_projeto RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO estoque_material_projeto (projeto_id, material_id, quantidade, localizacao)
            VALUES (%s, %s, %s, %s)
        """, (
            int(row['projeto_id']), int(row['material_id']),
            int(row['quantidade']), row.get('localizacao', 'N/A')
        ))
    print(f"   ✅ estoque_material_projeto: {len(df)} registros")


def run():
    print(f"\n📦 Seed {MIGRATION_REF} - Carregando modelo relacional...")

    print("\n   📖 Lendo CSVs...")
    df_programas        = pd.read_csv(CSV_DIR / 'programas.csv')
    df_projetos         = pd.read_csv(CSV_DIR / 'projetos_corrigido.csv')
    df_tarefas          = pd.read_csv(CSV_DIR / 'tarefas_projeto_corrigido.csv')
    df_materiais        = pd.read_csv(CSV_DIR / 'materiais.csv')
    df_fornecedores     = pd.read_csv(CSV_DIR / 'fornecedores.csv')
    df_tempo_tarefas    = pd.read_csv(CSV_DIR / 'tempo_tarefas_corrigido.csv')
    df_empenho          = pd.read_csv(CSV_DIR / 'empenho_materiais_corrigido.csv')
    df_solicitacoes     = pd.read_csv(CSV_DIR / 'solicitacoes_compra_corrigido.csv')
    df_pedidos          = pd.read_csv(CSV_DIR / 'pedidos_compra_corrigido.csv')
    df_compras_projeto  = pd.read_csv(CSV_DIR / 'compras_projeto.csv')
    df_estoque          = pd.read_csv(CSV_DIR / 'estoque_materiais_projeto.csv')
    print("   ✅ CSVs carregados")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("\n   📥 Carregando tabelas relacionais...")
        carregar_programa(df_programas, cursor)
        carregar_fornecedor(df_fornecedores, cursor)
        carregar_material(df_materiais, cursor)
        carregar_projeto(df_projetos, cursor)
        carregar_tarefa(df_tarefas, cursor)
        carregar_tempo_tarefa(df_tempo_tarefas, cursor)
        carregar_pedido_compra(df_pedidos, cursor)
        carregar_compras_projeto(df_compras_projeto, cursor)
        carregar_solicitacao_compra(df_solicitacoes, cursor)
        carregar_empenho_material(df_empenho, cursor)
        carregar_estoque_material_projeto(df_estoque, cursor)

        conn.commit()
        print(f"\n   ✅ Seed {MIGRATION_REF} concluído com sucesso!")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


class Command(BaseCommand):
    help = f'Seed {MIGRATION_REF}: popula as tabelas do modelo relacional'

    def handle(self, *args, **options):
        run()
