import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import os
from pathlib import Path

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'database'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def executar_sql_inicializacao(cursor, conn):
    current_dir = Path(__file__).parent
    sql_file = current_dir / 'star_model_tables' / 'tables.sql'
    
    if not sql_file.exists():
        print(f"⚠️  Arquivo SQL não encontrado em: {sql_file}")
        return
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    for statement in statements:
        try:
            cursor.execute(statement)
        except Exception as e:
            conn.rollback()
            print(f"❌ Erro ao executar SQL: {e}")
            raise
    
    print("   ✅ Tabelas do modelo estrela criadas/verificadas")


def carregar_dim_programa(df, cursor):
    cursor.execute("TRUNCATE TABLE dim_programa RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_programa (id, codigo_programa, nome_programa, gerente_programa, 
                                      data_inicio, data_fim_prevista, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                codigo_programa = EXCLUDED.codigo_programa,
                nome_programa = EXCLUDED.nome_programa,
                gerente_programa = EXCLUDED.gerente_programa,
                data_inicio = EXCLUDED.data_inicio,
                data_fim_prevista = EXCLUDED.data_fim_prevista,
                status = EXCLUDED.status
        """, (
            row['id'], row['codigo_programa'], row['nome_programa'],
            row['gerente_programa'],
            row['data_inicio'], row['data_fim_prevista'], row['status']
        ))
    print(f"   ✅ dim_programa: {len(df)} registros")


def carregar_dim_projeto(df, cursor):
    cursor.execute("TRUNCATE TABLE dim_projeto RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_projeto (id, codigo_projeto, nome_projeto, programa_id, responsavel,
                                     custo_hora, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                codigo_projeto = EXCLUDED.codigo_projeto,
                nome_projeto = EXCLUDED.nome_projeto,
                programa_id = EXCLUDED.programa_id,
                responsavel = EXCLUDED.responsavel,
                custo_hora = EXCLUDED.custo_hora,
                status = EXCLUDED.status
        """, (
            row['id'], row['codigo_projeto'], row['nome_projeto'],
            row['programa_id'], row['responsavel'], row['custo_hora'],
            row['status']
        ))
    print(f"   ✅ dim_projeto: {len(df)} registros")


def carregar_dim_tarefa(df, cursor):
    cursor.execute("TRUNCATE TABLE dim_tarefa RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_tarefa (id, codigo_tarefa, projeto_id, titulo, responsavel,
                                    horas_estimadas, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                codigo_tarefa = EXCLUDED.codigo_tarefa,
                projeto_id = EXCLUDED.projeto_id,
                titulo = EXCLUDED.titulo,
                responsavel = EXCLUDED.responsavel,
                horas_estimadas = EXCLUDED.horas_estimadas,
                status = EXCLUDED.status
        """, (
            row['id'], row['codigo_tarefa'], row['projeto_id'], row['titulo'],
            row['responsavel'], row['estimativa_horas'], row['status']
        ))
    print(f"   ✅ dim_tarefa: {len(df)} registros")


def carregar_dim_material(df, cursor):
    cursor.execute("TRUNCATE TABLE dim_material RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_material (id, codigo_material, descricao, categoria, 
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
            row['id'], row['codigo_material'], row['descricao'],
            row['categoria'], row['fabricante'], row['custo_estimado'], row['status']
        ))
    print(f"   ✅ dim_material: {len(df)} registros")


def carregar_dim_fornecedor(df, cursor):
    cursor.execute("TRUNCATE TABLE dim_fornecedor RESTART IDENTITY CASCADE;")
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_fornecedor (id, codigo_fornecedor, razao_social, cidade,
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
            row['id'], row['codigo_fornecedor'], row['razao_social'],
            row['cidade'], row['estado'], row['categoria'], row['status']
        ))
    print(f"   ✅ dim_fornecedor: {len(df)} registros")


def carregar_dim_funcionario(df_tempo, cursor):
    nomes_unicos = df_tempo['usuario'].dropna().unique()
    cursor.execute("TRUNCATE TABLE dim_funcionario RESTART IDENTITY CASCADE;")
    for idx, nome in enumerate(nomes_unicos, 1):
        cursor.execute("""
            INSERT INTO dim_funcionario (id, nome)
            VALUES (%s, %s)
            ON CONFLICT (nome) DO NOTHING
        """, (idx, nome))
    print(f"   ✅ dim_funcionario: {len(nomes_unicos)} registros")


def carregar_dim_status_pedido(cursor):
    status_list = [
        ('Aberto', 'Pendente', 1),
        ('Enviado', 'Pendente', 2),
        ('Parcialmente Entregue', 'Pendente', 3),
        ('Entregue', 'Concluído', 4),
        ('Cancelado', 'Cancelado', 5),
    ]
    cursor.execute("TRUNCATE TABLE dim_status_pedido RESTART IDENTITY CASCADE;")
    for nome, categoria, ordem in status_list:
        cursor.execute("""
            INSERT INTO dim_status_pedido (nome_status, categoria, ordem_prioridade)
            VALUES (%s, %s, %s)
            ON CONFLICT (nome_status) DO NOTHING
        """, (nome, categoria, ordem))
    print(f"   ✅ dim_status_pedido: {len(status_list)} registros")


def carregar_dim_tempo(cursor):
    cursor.execute("TRUNCATE TABLE dim_tempo RESTART IDENTITY CASCADE;")
    
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2026, 12, 31)
    
    registros = 0
    current_date = start_date
    
    while current_date <= end_date:
        tempo_id = int(current_date.strftime('%Y%m%d'))
        cursor.execute("""
            INSERT INTO dim_tempo (id, data, ano, mes, trimestre, semestre, dia_semana)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            tempo_id,
            current_date,
            current_date.year,
            current_date.month,
            (current_date.month - 1) // 3 + 1,
            1 if current_date.month <= 6 else 2,
            current_date.weekday()
        ))
        registros += 1
        current_date = current_date + timedelta(days=1)
    
    print(f"   ✅ dim_tempo: {registros} registros")


def carregar_fato_horas(df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor):
    cursor.execute("TRUNCATE TABLE fato_horas RESTART IDENTITY CASCADE;")
    
    projeto_programa = dict(zip(df_projetos['id'], df_projetos['programa_id']))
    projeto_custo = dict(zip(df_projetos['id'], df_projetos['custo_hora']))
    funcionario_map = {row['nome']: row['id'] for _, row in df_funcionario.iterrows()}
    
    registros = 0
    for _, row in df_tempo.iterrows():
        horas = row['horas_trabalhadas']
        if pd.isna(horas) or horas <= 0:
            continue
        
        data = pd.to_datetime(row['data'])
        tempo_id = int(data.strftime('%Y%m%d'))
        
        tarefa_id = int(row['tarefa_id'])
        tarefa_row = df_tarefas[df_tarefas['id'] == tarefa_id]
        if tarefa_row.empty:
            continue
        projeto_id = int(tarefa_row.iloc[0]['projeto_id'])
        
        programa_id = int(projeto_programa.get(projeto_id))
        custo_hora = float(projeto_custo.get(projeto_id, 0))
        custo_horas = float(horas) * custo_hora
        
        funcionario_id = int(funcionario_map.get(row['usuario'], 1))
        
        cursor.execute("""
            INSERT INTO fato_horas (tempo_id, projeto_id, programa_id, tarefa_id,
                                    funcionario_id, horas_trabalhadas, custo_horas)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (tempo_id, projeto_id, programa_id, tarefa_id,
              funcionario_id, float(horas), custo_horas))
        registros += 1
    
    print(f"   ✅ fato_horas: {registros} registros")


def carregar_fato_materiais(df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, cursor):
    cursor.execute("TRUNCATE TABLE fato_materiais RESTART IDENTITY CASCADE;")
    
    projeto_programa = dict(zip(df_projetos['id'], df_projetos['programa_id']))
    material_custo = dict(zip(df_materiais['id'], df_materiais['custo_estimado']))
    
    registros = 0
    for _, row in df_empenho.iterrows():
        data = pd.to_datetime(row['data_empenho'])
        tempo_id = int(data.strftime('%Y%m%d'))
        
        projeto_id = int(row['projeto_id'])
        programa_id = int(projeto_programa.get(projeto_id))
        material_id = int(row['material_id'])
        fornecedor_id = int(row['fornecedor_id']) if pd.notna(row.get('fornecedor_id')) else None
        custo_material = float(material_custo.get(material_id, 0))
        custo_materiais = float(row['quantidade_empenhada']) * custo_material
        
        cursor.execute("""
            INSERT INTO fato_materiais (tempo_id, projeto_id, programa_id, material_id,
                                        fornecedor_id, quantidade_empenhada, custo_materiais)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (tempo_id, projeto_id, programa_id, material_id,
              fornecedor_id, int(row['quantidade_empenhada']), custo_materiais))
        registros += 1
    
    print(f"   ✅ fato_materiais: {registros} registros")


def carregar_fato_compras(df_solicitacoes, df_pedidos, df_compras_projeto, df_projetos, 
                          df_materiais, df_fornecedores, df_status_pedido, cursor):
    cursor.execute("TRUNCATE TABLE fato_compras RESTART IDENTITY CASCADE;")
    
    status_map = {row['nome_status']: row['id'] for _, row in df_status_pedido.iterrows()}
    
    df_compras = df_solicitacoes.merge(
        df_pedidos, left_on='id', right_on='solicitacao_id', suffixes=('_sol', '_ped')
    )
    
    df_compras = df_compras.merge(
        df_compras_projeto[['pedido_compra_id', 'valor_alocado']],
        left_on='id_ped', right_on='pedido_compra_id',
        how='left'
    )
    
    registros = 0
    for _, row in df_compras.iterrows():
        data = pd.to_datetime(row['data_solicitacao'])
        tempo_id = int(data.strftime('%Y%m%d'))
        
        lead_time = None
        if pd.notna(row.get('data_previsao_entrega')) and pd.notna(row.get('data_pedido')):
            previsao = pd.to_datetime(row['data_previsao_entrega'])
            pedido = pd.to_datetime(row['data_pedido'])
            lead_time = (previsao - pedido).days
        
        status_id = int(status_map.get(row['status_ped'], 1))
        
        cursor.execute("""
            INSERT INTO fato_compras (tempo_id, projeto_id, material_id, fornecedor_id, status_id,
                                      quantidade_solicitada, valor_alocado, valor_total, 
                                      lead_time, data_previsao_entrega)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            tempo_id, int(row['projeto_id']), int(row['material_id']), int(row['fornecedor_id']), status_id,
            int(row['quantidade']), float(row.get('valor_alocado', 0)), float(row['valor_total']),
            lead_time, row.get('data_previsao_entrega')
        ))
        registros += 1
    
    print(f"   ✅ fato_compras: {registros} registros")


def carregar_fato_estoque(df_estoque, df_projetos, cursor):
    cursor.execute("TRUNCATE TABLE fato_estoque RESTART IDENTITY CASCADE;")
    
    data_snapshot = datetime.now().date()
    tempo_id = int(data_snapshot.strftime('%Y%m%d'))
    
    registros = 0
    for _, row in df_estoque.iterrows():
        cursor.execute("""
            INSERT INTO fato_estoque (tempo_id, material_id, projeto_id, quantidade_estoque)
            VALUES (%s, %s, %s, %s)
        """, (tempo_id, int(row['material_id']), int(row['projeto_id']), int(row['quantidade'])))
        registros += 1
    
    print(f"   ✅ fato_estoque: {registros} registros")


def main():
    print("=" * 70)
    print("🚀 ETL - MODELO ESTRELA LUNAE")
    print("=" * 70)
    
    csv_dir = Path(__file__).parent / 'corrected_documents'
    
    print("\n📖 Carregando arquivos CSV...")
    
    df_programas = pd.read_csv(csv_dir / 'programas.csv')
    df_projetos = pd.read_csv(csv_dir / 'projetos_corrigido.csv')
    df_tarefas = pd.read_csv(csv_dir / 'tarefas_projeto_corrigido.csv')
    df_materiais = pd.read_csv(csv_dir / 'materiais.csv')
    df_fornecedores = pd.read_csv(csv_dir / 'fornecedores.csv')
    df_tempo_tarefas = pd.read_csv(csv_dir / 'tempo_tarefas_corrigido.csv')
    df_empenho = pd.read_csv(csv_dir / 'empenho_materiais.csv')
    df_solicitacoes = pd.read_csv(csv_dir / 'solicitacoes_compra.csv')
    df_pedidos = pd.read_csv(csv_dir / 'pedidos_compra.csv')
    df_compras_projeto = pd.read_csv(csv_dir / 'compras_projeto.csv')
    df_estoque = pd.read_csv(csv_dir / 'estoque_materiais_projeto.csv')
    
    print("   ✅ Todos os arquivos carregados")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        print("\n🛠️  Inicializando banco de dados...")
        executar_sql_inicializacao(cursor, conn)
        
        print("\n📦 Carregando dimensões...")
        
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
        
        print("\n📊 Carregando tabelas fato...")
        
        carregar_fato_horas(df_tempo_tarefas, df_tarefas, df_projetos, df_programas, df_funcionario, cursor)
        carregar_fato_materiais(df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, cursor)
        
        cursor.execute("SELECT id, nome_status FROM dim_status_pedido")
        df_status_pedido = pd.DataFrame(cursor.fetchall(), columns=['id', 'nome_status'])
        
        carregar_fato_compras(df_solicitacoes, df_pedidos, df_compras_projeto, df_projetos,
                              df_materiais, df_fornecedores, df_status_pedido, cursor)
        carregar_fato_estoque(df_estoque, df_projetos, cursor)
        
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ ETL CONCLUÍDO COM SUCESSO!")
        print("=" * 70)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro durante o ETL: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
