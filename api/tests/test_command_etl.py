import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'management', 'commands'))

from command_etl import (
    executar_sql_inicializacao,
    carregar_dim_programa,
    carregar_dim_projeto,
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
    main,
)


class TestGetConnection:
    @patch.dict(os.environ, {
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_PORT': '5432',
        'POSTGRES_DB': 'test_db',
        'POSTGRES_USER': 'test_user',
        'POSTGRES_PASSWORD': 'test_pass'
    })
    @patch('psycopg2.connect')
    def test_get_connection_com_variaveis_ambiente(self, mock_connect):
        from command_etl import get_connection as gc
        gc()
        mock_connect.assert_called_once()


class TestExecutarSqlInicializacao:
    @patch('builtins.open', create=True)
    @patch('pathlib.Path.exists', return_value=True)
    def test_executar_sql_com_sucesso(self, mock_exists, mock_open):
        cursor = MagicMock()
        conn = MagicMock()
        
        sql_content = """
        DROP TABLE IF EXISTS test;
        CREATE TABLE test (id INT);
        INSERT INTO test VALUES (1);
        """
        
        mock_open.return_value.__enter__.return_value.read.return_value = sql_content
        
        with patch('builtins.print'):
            executar_sql_inicializacao(cursor, conn)
        
        assert cursor.execute.call_count >= 3

    @patch('pathlib.Path.exists', return_value=False)
    def test_arquivo_sql_nao_encontrado(self, mock_exists):
        cursor = MagicMock()
        conn = MagicMock()
        
        with patch('builtins.print'):
            executar_sql_inicializacao(cursor, conn)
        
        cursor.execute.assert_not_called()

    @patch('builtins.open', create=True)
    @patch('pathlib.Path.exists', return_value=True)
    def test_executar_sql_com_erro(self, mock_exists, mock_open):
        cursor = MagicMock()
        conn = MagicMock()
        
        sql_content = "SELECT * FROM nonexistent;"
        mock_open.return_value.__enter__.return_value.read.return_value = sql_content
        cursor.execute.side_effect = Exception("Table not found")
        
        with pytest.raises(Exception):
            executar_sql_inicializacao(cursor, conn)
        
        conn.rollback.assert_called_once()


class TestCarregarDimPrograma:
    def test_carregar_dim_programa_com_sucesso(self):
        df = pd.DataFrame({
            'id': [1, 2],
            'codigo_programa': ['PROG001', 'PROG002'],
            'nome_programa': ['Programa 1', 'Programa 2'],
            'gerente_programa': ['João', 'Maria'],
            'data_inicio': ['2026-01-01', '2026-02-01'],
            'data_fim_prevista': ['2026-12-31', '2026-12-31'],
            'status': ['Em andamento', 'Concluído']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_programa(df, cursor)
        
        assert cursor.execute.call_count == len(df) + 1

    def test_carregar_dim_programa_vazio(self):
        df = pd.DataFrame({
            'id': [],
            'codigo_programa': [],
            'nome_programa': [],
            'gerente_programa': [],
            'data_inicio': [],
            'data_fim_prevista': [],
            'status': []
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_programa(df, cursor)
        
        cursor.execute.assert_called_once_with("TRUNCATE TABLE dim_programa RESTART IDENTITY CASCADE;")

    def test_carregar_dim_programa_com_nulos(self):
        df = pd.DataFrame({
            'id': [1],
            'codigo_programa': ['PROG001'],
            'nome_programa': ['Programa 1'],
            'gerente_programa': [None],
            'data_inicio': ['2026-01-01'],
            'data_fim_prevista': [None],
            'status': ['Em andamento']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_programa(df, cursor)
        
        args = cursor.execute.call_args_list[1][0]
        assert args[1][3] is None


class TestCarregarDimProjeto:
    def test_carregar_dim_projeto_com_sucesso(self):
        df = pd.DataFrame({
            'id': [1, 2],
            'codigo_projeto': ['PROJ001', 'PROJ002'],
            'nome_projeto': ['Projeto 1', 'Projeto 2'],
            'programa_id': [1, 1],
            'responsavel': ['Pedro', 'Ana'],
            'custo_hora': [100.0, 150.0],
            'status': ['Em andamento', 'Concluído']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_projeto(df, cursor)
        
        assert cursor.execute.call_count == len(df) + 1

    def test_carregar_dim_projeto_tipos_numericos(self):
        df = pd.DataFrame({
            'id': np.array([1], dtype=np.int64),
            'codigo_projeto': ['PROJ001'],
            'nome_projeto': ['Projeto 1'],
            'programa_id': np.array([1], dtype=np.int64),
            'responsavel': ['Pedro'],
            'custo_hora': np.array([100.0], dtype=np.float64),
            'status': ['Em andamento']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_projeto(df, cursor)
        
        args = cursor.execute.call_args_list[1][0]
        assert isinstance(args[1][0], (int, np.integer))


class TestCarregarDimTarefa:
    def test_carregar_dim_tarefa_com_sucesso(self):
        df = pd.DataFrame({
            'id': [1, 2],
            'codigo_tarefa': ['TAR001', 'TAR002'],
            'projeto_id': [1, 1],
            'titulo': ['Tarefa 1', 'Tarefa 2'],
            'responsavel': ['João', 'Maria'],
            'estimativa_horas': [40.0, 80.0],
            'status': ['Em andamento', 'Concluída']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_tarefa(df, cursor)
        
        assert cursor.execute.call_count == len(df) + 1

    def test_carregar_dim_tarefa_com_horas_nulas(self):
        df = pd.DataFrame({
            'id': [1],
            'codigo_tarefa': ['TAR001'],
            'projeto_id': [1],
            'titulo': ['Tarefa 1'],
            'responsavel': ['João'],
            'estimativa_horas': [None],
            'status': ['Em andamento']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_tarefa(df, cursor)
        
        args = cursor.execute.call_args_list[1][0]
        assert args[1][5] is None


class TestCarregarDimMaterial:
    def test_carregar_dim_material_com_sucesso(self):
        df = pd.DataFrame({
            'id': [1, 2],
            'codigo_material': ['MAT001', 'MAT002'],
            'descricao': ['Material 1', 'Material 2'],
            'categoria': ['Eletrônico', 'Hidráulico'],
            'fabricante': ['Fab1', 'Fab2'],
            'custo_estimado': [50.0, 100.0],
            'status': ['Ativo', 'Ativo']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_material(df, cursor)
        
        assert cursor.execute.call_count == len(df) + 1


class TestCarregarDimFornecedor:
    def test_carregar_dim_fornecedor_com_sucesso(self):
        df = pd.DataFrame({
            'id': [1, 2],
            'codigo_fornecedor': ['FOR001', 'FOR002'],
            'razao_social': ['Fornecedor 1', 'Fornecedor 2'],
            'cidade': ['São Paulo', 'Rio de Janeiro'],
            'estado': ['SP', 'RJ'],
            'categoria': ['Eletrônicos', 'Hidráulicos'],
            'status': ['Ativo', 'Ativo']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_fornecedor(df, cursor)
        
        assert cursor.execute.call_count == len(df) + 1


class TestCarregarDimFuncionario:
    def test_carregar_dim_funcionario_com_sucesso(self):
        df = pd.DataFrame({
            'usuario': ['João', 'Maria', 'Pedro', None]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_funcionario(df, cursor)
        
        assert cursor.execute.call_count == 4

    def test_carregar_dim_funcionario_sem_nulos(self):
        df = pd.DataFrame({
            'usuario': ['João', 'Maria', 'Pedro']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_funcionario(df, cursor)
        
        assert cursor.execute.call_count == 4 

    def test_carregar_dim_funcionario_todos_nulos(self):
        df = pd.DataFrame({
            'usuario': [None, None]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_funcionario(df, cursor)
        
        assert cursor.execute.call_count == 1 


class TestCarregarDimStatusPedido:
    def test_carregar_dim_status_pedido(self):
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_status_pedido(cursor)
        
        assert cursor.execute.call_count == 6

    def test_carregar_dim_status_pedido_valores(self):
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_status_pedido(cursor)
        
        calls = cursor.execute.call_args_list
        assert any('Entregue' in str(call) for call in calls)


class TestCarregarDimTempo:
    def test_carregar_dim_tempo(self):
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_tempo(cursor)
        
        assert cursor.execute.call_count >= 1826

    def test_carregar_dim_tempo_chamadas_corretas(self):
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_tempo(cursor)
        
        assert "TRUNCATE" in str(cursor.execute.call_args_list[0])


class TestCarregarFatoHoras:
    def test_carregar_fato_horas_com_sucesso(self):
        df_tempo = pd.DataFrame({
            'data': ['2026-01-01', '2026-01-02'],
            'tarefa_id': [1, 2],
            'usuario': ['João', 'Maria'],
            'horas_trabalhadas': [8.0, 10.0]
        })
        
        df_tarefas = pd.DataFrame({
            'id': [1, 2],
            'projeto_id': [10, 10]
        })
        
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [100],
            'custo_hora': [100.0]
        })
        
        df_programas = pd.DataFrame({
            'id': [100]
        })
        
        df_funcionario = pd.DataFrame({
            'nome': ['João', 'Maria'],
            'id': [1, 2]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_horas(df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor)
        
        assert cursor.execute.call_count == 3

    def test_carregar_fato_horas_sem_horas_validas(self):
        df_tempo = pd.DataFrame({
            'data': ['2026-01-01'],
            'tarefa_id': [1],
            'usuario': ['João'],
            'horas_trabalhadas': [0.0]
        })
        
        df_tarefas = pd.DataFrame({
            'id': [1],
            'projeto_id': [10]
        })
        
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [100],
            'custo_hora': [100.0]
        })
        
        df_programas = pd.DataFrame({
            'id': [100]
        })
        
        df_funcionario = pd.DataFrame({
            'nome': ['João'],
            'id': [1]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_horas(df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor)
        
        assert cursor.execute.call_count == 1

    def test_carregar_fato_horas_tarefa_inexistente(self):
        df_tempo = pd.DataFrame({
            'data': ['2026-01-01'],
            'tarefa_id': [999],
            'usuario': ['João'],
            'horas_trabalhadas': [8.0]
        })
        
        df_tarefas = pd.DataFrame({
            'id': [1],
            'projeto_id': [10]
        })
        
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [100],
            'custo_hora': [100.0]
        })
        
        df_programas = pd.DataFrame({
            'id': [100]
        })
        
        df_funcionario = pd.DataFrame({
            'nome': ['João'],
            'id': [1]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_horas(df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor)
        
        assert cursor.execute.call_count == 1


class TestCarregarFatoMateriais:
    def test_carregar_fato_materiais_com_sucesso(self):
        df_empenho = pd.DataFrame({
            'data_empenho': ['2026-01-01', '2026-01-02'],
            'projeto_id': [10, 10],
            'material_id': [1, 2],
            'fornecedor_id': [100, 101],
            'quantidade_empenhada': [10, 20]
        })
        
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [100]
        })
        
        df_programas = pd.DataFrame({'id': [100]})
        
        df_materiais = pd.DataFrame({
            'id': [1, 2],
            'custo_estimado': [50.0, 100.0]
        })
        
        df_fornecedores = pd.DataFrame({
            'id': [100, 101]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_materiais(df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, cursor)
        
        assert cursor.execute.call_count == 3

    def test_carregar_fato_materiais_fornecedor_nulo(self):
        df_empenho = pd.DataFrame({
            'data_empenho': ['2026-01-01'],
            'projeto_id': [10],
            'material_id': [1],
            'fornecedor_id': [None],
            'quantidade_empenhada': [10]
        })
        
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [100]
        })
        
        df_programas = pd.DataFrame({'id': [100]})
        
        df_materiais = pd.DataFrame({
            'id': [1],
            'custo_estimado': [50.0]
        })
        
        df_fornecedores = pd.DataFrame({'id': [100]})
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_materiais(df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, cursor)
        
        assert cursor.execute.call_count == 2
        
        args = cursor.execute.call_args_list[1][0]
        assert args[1][4] is None


class TestCarregarFatoCompras:
    def test_carregar_fato_compras_com_sucesso(self):
        df_solicitacoes = pd.DataFrame({
            'id': [1, 2],
            'data_solicitacao': ['2026-01-01', '2026-01-02'],
            'status': ['Aberto', 'Aberto']
        })
        
        df_pedidos = pd.DataFrame({
            'id': [10, 11],
            'solicitacao_id': [1, 2],
            'data_pedido': ['2026-01-01', '2026-01-02'],
            'status': ['Entregue', 'Enviado'],
            'projeto_id': [1, 1],
            'material_id': [1, 1],
            'fornecedor_id': [1, 1],
            'quantidade': [10, 20],
            'valor_total': [1000.0, 2000.0]
        })
        
        df_compras_projeto = pd.DataFrame({
            'pedido_compra_id': [10, 11],
            'valor_alocado': [1000.0, 2000.0]
        })
        
        df_projetos = pd.DataFrame({
            'id': [1]
        })
        
        df_materiais = pd.DataFrame({
            'id': [1]
        })
        
        df_fornecedores = pd.DataFrame({
            'id': [1]
        })
        
        df_status_pedido = pd.DataFrame({
            'nome_status': ['Entregue', 'Enviado'],
            'id': [1, 2]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_compras(
                df_solicitacoes, df_pedidos, df_compras_projeto, 
                df_projetos, df_materiais, df_fornecedores, df_status_pedido, cursor
            )
        
        assert cursor.execute.call_count >= 1

    def test_carregar_fato_compras_sem_lead_time(self):
        df_solicitacoes = pd.DataFrame({
            'id': [1],
            'data_solicitacao': ['2026-01-01'],
            'status': ['Aberto']
        })
        
        df_pedidos = pd.DataFrame({
            'id': [10],
            'solicitacao_id': [1],
            'data_pedido': [None],
            'status': ['Entregue'],
            'projeto_id': [1],
            'material_id': [1],
            'fornecedor_id': [1],
            'quantidade': [10],
            'valor_total': [1000.0]
        })
        
        df_compras_projeto = pd.DataFrame({
            'pedido_compra_id': [10],
            'valor_alocado': [1000.0]
        })
        
        df_projetos = pd.DataFrame({'id': [1]})
        df_materiais = pd.DataFrame({'id': [1]})
        df_fornecedores = pd.DataFrame({'id': [1]})
        
        df_status_pedido = pd.DataFrame({
            'nome_status': ['Entregue'],
            'id': [1]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_compras(
                df_solicitacoes, df_pedidos, df_compras_projeto, 
                df_projetos, df_materiais, df_fornecedores, df_status_pedido, cursor
            )
        
        args = cursor.execute.call_args_list
        if len(args) > 1:
            insert_call = args[1][0]
            assert 'lead_time' in str(insert_call)


class TestCarregarFatoEstoque:
    def test_carregar_fato_estoque_com_sucesso(self):
        df_estoque = pd.DataFrame({
            'material_id': [1, 2],
            'projeto_id': [10, 10],
            'quantidade': [100, 200]
        })
        
        df_projetos = pd.DataFrame({
            'id': [10]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_estoque(df_estoque, df_projetos, cursor)
        
        assert cursor.execute.call_count == 3

    def test_carregar_fato_estoque_vazio(self):
        df_estoque = pd.DataFrame({
            'material_id': [],
            'projeto_id': [],
            'quantidade': []
        })
        
        df_projetos = pd.DataFrame({
            'id': [10]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_estoque(df_estoque, df_projetos, cursor)
        
        assert cursor.execute.call_count == 1


class TestMain:
    @patch('command_etl.get_connection')
    @patch('command_etl.pd.read_csv')
    def test_main_com_sucesso(self, mock_read_csv, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        df_vazio_programa = pd.DataFrame({
            'id': [], 'codigo_programa': [], 'nome_programa': [],
            'gerente_programa': [], 'data_inicio': [],
            'data_fim_prevista': [], 'status': []
        })
        df_vazio_projeto = pd.DataFrame({
            'id': [], 'codigo_projeto': [], 'nome_projeto': [],
            'programa_id': [], 'responsavel': [],
            'custo_hora': [], 'status': []
        })
        df_vazio_tarefa = pd.DataFrame({
            'id': [], 'codigo_tarefa': [], 'projeto_id': [],
            'titulo': [], 'responsavel': [],
            'estimativa_horas': [], 'status': []
        })
        df_vazio_material = pd.DataFrame({
            'id': [], 'codigo_material': [], 'descricao': [],
            'categoria': [], 'fabricante': [],
            'custo_estimado': [], 'status': []
        })
        df_vazio_fornecedor = pd.DataFrame({
            'id': [], 'codigo_fornecedor': [], 'razao_social': [],
            'cidade': [], 'estado': [],
            'categoria': [], 'status': []
        })
        df_vazio_tempo_tarefas = pd.DataFrame({
            'usuario': []
        })
        df_vazio_empenho = pd.DataFrame({
            'data_empenho': [], 'projeto_id': [],
            'material_id': [], 'fornecedor_id': [],
            'quantidade_empenhada': []
        })
        df_vazio_solicitacoes = pd.DataFrame({
            'id': [], 'data_solicitacao': []
        })
        df_vazio_pedidos = pd.DataFrame({
            'id': [], 'solicitacao_id': [],
            'data_pedido': [], 'status': []
        })
        df_vazio_compras_projeto = pd.DataFrame({
            'pedido_compra_id': [], 'valor_alocado': []
        })
        df_vazio_estoque = pd.DataFrame({
            'material_id': [], 'projeto_id': [],
            'quantidade': []
        })
        
        mock_read_csv.side_effect = [
            df_vazio_programa, df_vazio_projeto, df_vazio_tarefa,
            df_vazio_material, df_vazio_fornecedor, df_vazio_tempo_tarefas,
            df_vazio_empenho, df_vazio_solicitacoes, df_vazio_pedidos,
            df_vazio_compras_projeto, df_vazio_estoque
        ]
        
        mock_cursor.fetchall.return_value = []
        
        with patch('builtins.open', create=True):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.print'):
                    main()
        
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('command_etl.get_connection')
    @patch('command_etl.pd.read_csv')
    def test_main_com_erro(self, mock_read_csv, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_read_csv.side_effect = FileNotFoundError("Arquivo não encontrado")
        
        with patch('builtins.print'):
            with pytest.raises(FileNotFoundError):
                main()
        
        mock_get_connection.assert_not_called()

    @patch('command_etl.get_connection')
    @patch('command_etl.pd.read_csv')
    def test_main_com_erro_na_execucao_sql(self, mock_read_csv, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        df_vazio = pd.DataFrame({
            'id': [], 'codigo_programa': [], 'nome_programa': [],
            'gerente_programa': [], 'data_inicio': [],
            'data_fim_prevista': [], 'status': []
        })
        mock_read_csv.return_value = df_vazio
        
        mock_cursor.execute.side_effect = Exception("SQL Error")
        
        with patch('builtins.open', create=True):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.print'):
                    with pytest.raises(Exception):
                        main()
        
        mock_conn.rollback.assert_called()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


class TestIntegracaoCoverage:
    def test_conversao_tipos_numpy_para_python(self):
        df = pd.DataFrame({
            'id': np.array([1, 2], dtype=np.int64),
            'codigo_programa': ['PROG001', 'PROG002'],
            'nome_programa': ['Programa 1', 'Programa 2'],
            'gerente_programa': ['João', 'Maria'],
            'data_inicio': ['2026-01-01', '2026-02-01'],
            'data_fim_prevista': ['2026-12-31', '2026-12-31'],
            'status': ['Em andamento', 'Concluído']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_programa(df, cursor)
        
        args = cursor.execute.call_args_list[1][0]
        assert all(isinstance(v, (int, str, type(None))) for v in args[1])

    def test_manipulacao_datas_diferentes_formatos(self):
        df_tempo = pd.DataFrame({
            'data': [pd.Timestamp('2026-01-01'), '2026-01-02'],
            'tarefa_id': [1, 2],
            'usuario': ['João', 'Maria'],
            'horas_trabalhadas': [8.0, 10.0]
        })
        
        df_tarefas = pd.DataFrame({
            'id': [1, 2],
            'projeto_id': [10, 10]
        })
        
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [100],
            'custo_hora': [100.0]
        })
        
        df_programas = pd.DataFrame({'id': [100]})
        
        df_funcionario = pd.DataFrame({
            'nome': ['João', 'Maria'],
            'id': [1, 2]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_horas(df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor)
        
        assert cursor.execute.call_count >= 1

    def test_calculo_custo_horas(self):
        df_tempo = pd.DataFrame({
            'data': ['2026-01-01'],
            'tarefa_id': [1],
            'usuario': ['João'],
            'horas_trabalhadas': [10.0]
        })
        
        df_tarefas = pd.DataFrame({
            'id': [1],
            'projeto_id': [10]
        })
        
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [100],
            'custo_hora': [100.0]
        })
        
        df_programas = pd.DataFrame({'id': [100]})
        df_funcionario = pd.DataFrame({
            'nome': ['João'],
            'id': [1]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_horas(df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor)
        
        args = cursor.execute.call_args_list[1][0]
        custo_horas = args[1][6]
        assert custo_horas == 1000.0

    def test_calculo_custo_materiais(self):
        df_empenho = pd.DataFrame({
            'data_empenho': ['2026-01-01'],
            'projeto_id': [10],
            'material_id': [1],
            'fornecedor_id': [100],
            'quantidade_empenhada': [10]
        })
        
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [100]
        })
        
        df_programas = pd.DataFrame({'id': [100]})
        
        df_materiais = pd.DataFrame({
            'id': [1],
            'custo_estimado': [50.0]
        })
        
        df_fornecedores = pd.DataFrame({'id': [100]})
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_materiais(df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, cursor)
        
        args = cursor.execute.call_args_list[1][0]
        custo_materiais = args[1][6]
        assert custo_materiais == 500.0

    def test_calculo_lead_time(self):
        df_solicitacoes = pd.DataFrame({
            'id': [1],
            'data_solicitacao': ['2026-01-01'],
            'status': ['Aberto']
        })
        
        df_pedidos = pd.DataFrame({
            'id': [10],
            'solicitacao_id': [1],
            'data_pedido': ['2026-01-05'],
            'status': ['Entregue'],
            'projeto_id': [1],
            'material_id': [1],
            'fornecedor_id': [1],
            'quantidade': [10],
            'valor_total': [1000.0]
        })
        
        df_compras_projeto = pd.DataFrame({
            'pedido_compra_id': [10],
            'valor_alocado': [1000.0]
        })
        
        df_projetos = pd.DataFrame({'id': [1]})
        df_materiais = pd.DataFrame({'id': [1]})
        df_fornecedores = pd.DataFrame({'id': [1]})
        
        df_status_pedido = pd.DataFrame({
            'nome_status': ['Entregue'],
            'id': [1]
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_compras(
                df_solicitacoes, df_pedidos, df_compras_projeto, 
                df_projetos, df_materiais, df_fornecedores, df_status_pedido, cursor
            )


class TestEdgeCases:
    def test_unicode_caracteres_especiais(self):
        df = pd.DataFrame({
            'id': [1],
            'codigo_programa': ['PROG_001'],
            'nome_programa': ['Programa com Açúcar e Caféína'],
            'gerente_programa': ['João da Silva'],
            'data_inicio': ['2026-01-01'],
            'data_fim_prevista': ['2026-12-31'],
            'status': ['Em andamento']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_programa(df, cursor)
        
        args = cursor.execute.call_args_list[1][0]
        assert 'Açúcar' in args[1][2]
        assert 'João' in args[1][3]

    def test_valores_muito_grandes(self):
        df_empenho = pd.DataFrame({
            'data_empenho': ['2026-01-01'],
            'projeto_id': [10],
            'material_id': [1],
            'fornecedor_id': [100],
            'quantidade_empenhada': [999999]
        })
        
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [100]
        })
        
        df_programas = pd.DataFrame({'id': [100]})
        
        df_materiais = pd.DataFrame({
            'id': [1],
            'custo_estimado': [9999.99]
        })
        
        df_fornecedores = pd.DataFrame({'id': [100]})
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_fato_materiais(df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, cursor)
        
        assert cursor.execute.call_count >= 2

    def test_valores_decimais_precisos(self):
        df = pd.DataFrame({
            'id': [1],
            'codigo_projeto': ['PROJ001'],
            'nome_projeto': ['Projeto 1'],
            'programa_id': [1],
            'responsavel': ['Pedro'],
            'custo_hora': [123.456],
            'status': ['Em andamento']
        })
        
        cursor = MagicMock()
        
        with patch('builtins.print'):
            carregar_dim_projeto(df, cursor)
        
        args = cursor.execute.call_args_list[1][0]
        assert args[1][5] == 123.456
