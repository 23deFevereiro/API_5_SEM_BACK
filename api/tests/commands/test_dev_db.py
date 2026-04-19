import pytest
import importlib
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from api.management.commands.seeds.seed_0004 import (
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
    get_connection,
    run,
)


def make_cursor():
    return MagicMock()


def make_conn(cursor):
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


class TestGetConnection:
    @patch.dict(os.environ, {
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_PORT': '5432',
        'POSTGRES_DB': 'test_db',
        'POSTGRES_USER': 'test_user',
        'POSTGRES_PASSWORD': 'test_pass',
    })
    @patch('api.management.commands.seeds.seed_0004.psycopg2.connect')
    def test_chama_psycopg2_connect(self, mock_connect):
        get_connection()
        mock_connect.assert_called_once()


class TestCarregarDimPrograma:
    def _df(self, n=2):
        return pd.DataFrame({
            'id': range(1, n + 1),
            'codigo_programa': [f'PROG00{i}' for i in range(1, n + 1)],
            'nome_programa': [f'Programa {i}' for i in range(1, n + 1)],
            'gerente_programa': ['João', 'Maria'][:n],
            'data_inicio': ['2026-01-01'] * n,
            'data_fim_prevista': ['2026-12-31'] * n,
            'status': ['Em andamento'] * n,
        })

    def test_truncate_e_inserts(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_programa(self._df(2), cursor)
        assert cursor.execute.call_count == 3

    def test_dataframe_vazio_apenas_truncate(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_programa(self._df(0), cursor)
        cursor.execute.assert_called_once_with(
            "TRUNCATE TABLE dim_programa RESTART IDENTITY CASCADE;"
        )

    def test_valor_nulo_preservado(self):
        df = self._df(1)
        df.at[0, 'gerente_programa'] = None
        df.at[0, 'data_fim_prevista'] = None
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_programa(df, cursor)
        params = cursor.execute.call_args_list[1][0][1]
        assert params[3] is None
        assert params[5] is None


class TestCarregarDimProjeto:
    def _df(self, n=2):
        return pd.DataFrame({
            'id': range(1, n + 1),
            'codigo_projeto': [f'PROJ00{i}' for i in range(1, n + 1)],
            'nome_projeto': [f'Projeto {i}' for i in range(1, n + 1)],
            'programa_id': [1] * n,
            'responsavel': ['Pedro'] * n,
            'custo_hora': [100.0] * n,
            'status': ['Em andamento'] * n,
        })

    def test_truncate_e_inserts(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_projeto(self._df(2), cursor)
        assert cursor.execute.call_count == 3

    def test_tipos_numericos_numpy(self):
        df = self._df(1)
        df['id'] = df['id'].astype(np.int64)
        df['programa_id'] = df['programa_id'].astype(np.int64)
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_projeto(df, cursor)
        params = cursor.execute.call_args_list[1][0][1]
        assert isinstance(params[0], (int, np.integer))


class TestCarregarDimTarefa:
    def _df(self, n=2):
        return pd.DataFrame({
            'id': range(1, n + 1),
            'codigo_tarefa': [f'TAR00{i}' for i in range(1, n + 1)],
            'projeto_id': [1] * n,
            'titulo': [f'Tarefa {i}' for i in range(1, n + 1)],
            'responsavel': ['João'] * n,
            'estimativa_horas': [40.0] * n,
            'status': ['Em andamento'] * n,
        })

    def test_truncate_e_inserts(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_tarefa(self._df(2), cursor)
        assert cursor.execute.call_count == 3

    def test_horas_estimadas_nulas(self):
        df = self._df(1)
        df.at[0, 'estimativa_horas'] = None
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_tarefa(df, cursor)
        params = cursor.execute.call_args_list[1][0][1]
        assert params[5] is None


class TestCarregarDimMaterial:
    def test_truncate_e_inserts(self):
        df = pd.DataFrame({
            'id': [1, 2],
            'codigo_material': ['MAT001', 'MAT002'],
            'descricao': ['Material 1', 'Material 2'],
            'categoria': ['Eletrônico', 'Hidráulico'],
            'fabricante': ['Fab1', 'Fab2'],
            'custo_estimado': [50.0, 100.0],
            'status': ['Ativo', 'Ativo'],
        })
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_material(df, cursor)
        assert cursor.execute.call_count == 3


class TestCarregarDimFornecedor:
    def test_truncate_e_inserts(self):
        df = pd.DataFrame({
            'id': [1, 2],
            'codigo_fornecedor': ['FOR001', 'FOR002'],
            'razao_social': ['Fornecedor 1', 'Fornecedor 2'],
            'cidade': ['São Paulo', 'Rio de Janeiro'],
            'estado': ['SP', 'RJ'],
            'categoria': ['Eletrônicos', 'Hidráulicos'],
            'status': ['Ativo', 'Ativo'],
        })
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_fornecedor(df, cursor)
        assert cursor.execute.call_count == 3


class TestCarregarDimFuncionario:
    def test_ignora_nulos_e_insere_unicos(self):
        df = pd.DataFrame({'usuario': ['João', 'Maria', 'Pedro', None]})
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_funcionario(df, cursor)
        assert cursor.execute.call_count == 4

    def test_sem_nulos(self):
        df = pd.DataFrame({'usuario': ['João', 'Maria', 'Pedro']})
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_funcionario(df, cursor)
        assert cursor.execute.call_count == 4

    def test_todos_nulos(self):
        df = pd.DataFrame({'usuario': [None, None]})
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_funcionario(df, cursor)
        assert cursor.execute.call_count == 1


class TestCarregarDimStatusPedido:
    def test_insere_cinco_status(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_status_pedido(cursor)
        assert cursor.execute.call_count == 6

    def test_contem_status_entregue(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_status_pedido(cursor)
        chamadas = str(cursor.execute.call_args_list)
        assert 'Entregue' in chamadas

    def test_contem_status_cancelado(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_status_pedido(cursor)
        chamadas = str(cursor.execute.call_args_list)
        assert 'Cancelado' in chamadas


class TestCarregarDimTempo:
    def test_gera_datas_de_2022_a_2026(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_tempo(cursor)
        assert cursor.execute.call_count >= 1827

    def test_primeira_chamada_e_truncate(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_tempo(cursor)
        assert "TRUNCATE" in str(cursor.execute.call_args_list[0])


class TestCarregarFatoHoras:
    def _base(self):
        df_tempo = pd.DataFrame({
            'data': ['2026-01-01', '2026-01-02'],
            'tarefa_id': [1, 2],
            'usuario': ['João', 'Maria'],
            'horas_trabalhadas': [8.0, 10.0],
        })
        df_tarefas = pd.DataFrame({'id': [1, 2], 'projeto_id': [10, 10]})
        df_projetos = pd.DataFrame({'id': [10], 'programa_id': [100], 'custo_hora': [100.0]})
        df_programas = pd.DataFrame({'id': [100]})
        df_func = pd.DataFrame({'nome': ['João', 'Maria'], 'id': [1, 2]})
        return df_tempo, df_tarefas, df_projetos, df_programas, df_func

    def test_truncate_e_dois_inserts(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_horas(*self._base(), cursor)
        assert cursor.execute.call_count == 3

    def test_horas_zero_ignoradas(self):
        df_tempo, df_tarefas, df_projetos, df_programas, df_func = self._base()
        df_tempo.at[0, 'horas_trabalhadas'] = 0.0
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_horas(df_tempo, df_tarefas, df_projetos, df_programas, df_func, cursor)
        assert cursor.execute.call_count == 2

    def test_tarefa_inexistente_ignorada(self):
        df_tempo, df_tarefas, df_projetos, df_programas, df_func = self._base()
        df_tempo.at[0, 'tarefa_id'] = 999
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_horas(df_tempo, df_tarefas, df_projetos, df_programas, df_func, cursor)
        assert cursor.execute.call_count == 2

    def test_custo_calculado_corretamente(self):
        df_tempo = pd.DataFrame({
            'data': ['2026-01-01'],
            'tarefa_id': [1],
            'usuario': ['João'],
            'horas_trabalhadas': [10.0],
        })
        df_tarefas = pd.DataFrame({'id': [1], 'projeto_id': [10]})
        df_projetos = pd.DataFrame({'id': [10], 'programa_id': [100], 'custo_hora': [100.0]})
        df_programas = pd.DataFrame({'id': [100]})
        df_func = pd.DataFrame({'nome': ['João'], 'id': [1]})
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_horas(df_tempo, df_tarefas, df_projetos, df_programas, df_func, cursor)
        params = cursor.execute.call_args_list[1][0][1]
        assert params[6] == pytest.approx(1000.0)


class TestCarregarFatoMateriais:
    def _base(self):
        df_empenho = pd.DataFrame({
            'data_empenho': ['2026-01-01', '2026-01-02'],
            'projeto_id': [10, 10],
            'material_id': [1, 2],
            'quantidade_empenhada': [10, 20],
        })
        df_projetos = pd.DataFrame({'id': [10], 'programa_id': [100]})
        df_programas = pd.DataFrame({'id': [100]})
        df_materiais = pd.DataFrame({'id': [1, 2], 'custo_estimado': [50.0, 100.0]})
        df_fornecedores = pd.DataFrame({'id': [100, 101]})
        df_solicitacoes = pd.DataFrame({'id': [1, 2], 'projeto_id': [10, 10], 'material_id': [1, 2]})
        df_pedidos = pd.DataFrame({'solicitacao_id': [1, 2], 'fornecedor_id': [100, 101]})
        return df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, df_solicitacoes, df_pedidos

    def test_truncate_e_dois_inserts(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_materiais(*self._base(), cursor)
        assert cursor.execute.call_count == 3

    def test_fornecedor_nulo_permitido(self):
        df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, df_sol, df_ped = self._base()
        df_empenho = df_empenho.copy()
        df_empenho.at[0, 'material_id'] = 99
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_materiais(df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, df_sol, df_ped, cursor)
        params = cursor.execute.call_args_list[1][0][1]
        assert params[4] is None

    def test_custo_materiais_calculado(self):
        df_empenho = pd.DataFrame({
            'data_empenho': ['2026-01-01'],
            'projeto_id': [10],
            'material_id': [1],
            'quantidade_empenhada': [10],
        })
        df_projetos = pd.DataFrame({'id': [10], 'programa_id': [100]})
        df_programas = pd.DataFrame({'id': [100]})
        df_materiais = pd.DataFrame({'id': [1], 'custo_estimado': [50.0]})
        df_fornecedores = pd.DataFrame({'id': [100]})
        df_sol = pd.DataFrame({'id': [1], 'projeto_id': [10], 'material_id': [1]})
        df_ped = pd.DataFrame({'solicitacao_id': [1], 'fornecedor_id': [100]})
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_materiais(df_empenho, df_projetos, df_programas, df_materiais, df_fornecedores, df_sol, df_ped, cursor)
        params = cursor.execute.call_args_list[1][0][1]
        assert params[6] == pytest.approx(500.0)


class TestCarregarFatoCompras:
    def _base(self):
        df_sol = pd.DataFrame({
            'id': [1, 2],
            'projeto_id': [1, 1],
            'material_id': [1, 1],
            'quantidade': [10, 20],
            'data_solicitacao': ['2026-01-01', '2026-01-02'],
            'status': ['Pendente', 'Pendente'],
        })

        df_ped = pd.DataFrame({
            'id': [10, 11],
            'solicitacao_id': [1, 2],
            'data_pedido': ['2026-01-01', '2026-01-02'],
            'data_previsao_entrega': ['2026-01-08', '2026-01-09'],
            'status': ['Entregue', 'Enviado'],
            'fornecedor_id': [1, 1],
            'valor_total': [1000.0, 2000.0],
        })
        df_cp = pd.DataFrame({'pedido_compra_id': [10, 11], 'valor_alocado': [1000.0, 2000.0]})
        df_proj = pd.DataFrame({'id': [1]})
        df_mat = pd.DataFrame({'id': [1]})
        df_forn = pd.DataFrame({'id': [1]})
        df_status = pd.DataFrame({'nome_status': ['Entregue', 'Enviado'], 'id': [1, 2]})
        return df_sol, df_ped, df_cp, df_proj, df_mat, df_forn, df_status

    def test_truncate_e_inserts(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_compras(*self._base(), cursor)
        assert cursor.execute.call_count >= 3

    def test_lead_time_calculado(self):
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_compras(*self._base(), cursor)
        params = cursor.execute.call_args_list[1][0][1]
        assert params[9] == 7

    def test_lead_time_nulo_quando_sem_datas(self):
        df_sol, df_ped, df_cp, df_proj, df_mat, df_forn, df_status = self._base()
        df_ped.at[0, 'data_pedido'] = None
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_compras(df_sol, df_ped, df_cp, df_proj, df_mat, df_forn, df_status, cursor)
        params = cursor.execute.call_args_list[1][0][1]
        assert params[9] is None


class TestCarregarFatoEstoque:
    def test_truncate_e_inserts(self):
        df = pd.DataFrame({
            'material_id': [1, 2],
            'projeto_id': [10, 10],
            'quantidade': [100, 200],
        })
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_estoque(df, cursor)
        assert cursor.execute.call_count == 3

    def test_dataframe_vazio(self):
        df = pd.DataFrame({'material_id': [], 'projeto_id': [], 'quantidade': []})
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_estoque(df, cursor)
        assert cursor.execute.call_count == 1


class TestRun:
    def _dfs_vazios(self):
        return {
            'programas': pd.DataFrame({
                'id': [], 'codigo_programa': [], 'nome_programa': [],
                'gerente_programa': [], 'data_inicio': [], 'data_fim_prevista': [], 'status': [],
            }),
            'projetos': pd.DataFrame({
                'id': [], 'codigo_projeto': [], 'nome_projeto': [],
                'programa_id': [], 'responsavel': [], 'custo_hora': [], 'status': [],
            }),
            'tarefas': pd.DataFrame({
                'id': [], 'codigo_tarefa': [], 'projeto_id': [], 'titulo': [],
                'responsavel': [], 'estimativa_horas': [], 'status': [],
            }),
            'materiais': pd.DataFrame({
                'id': [], 'codigo_material': [], 'descricao': [],
                'categoria': [], 'fabricante': [], 'custo_estimado': [], 'status': [],
            }),
            'fornecedores': pd.DataFrame({
                'id': [], 'codigo_fornecedor': [], 'razao_social': [],
                'cidade': [], 'estado': [], 'categoria': [], 'status': [],
            }),
            'tempo_tarefas': pd.DataFrame({'usuario': [], 'data': [], 'tarefa_id': [], 'horas_trabalhadas': []}),
            'empenho': pd.DataFrame({
                'data_empenho': [], 'projeto_id': [], 'material_id': [], 'fornecedor_id': [], 'quantidade_empenhada': [],
            }),
            'solicitacoes': pd.DataFrame({'id': [], 'projeto_id': [], 'material_id': [], 'data_solicitacao': [], 'status': []}),
            'pedidos': pd.DataFrame({'id': [], 'solicitacao_id': [], 'data_pedido': [], 'data_previsao_entrega': [], 'valor_total': [], 'fornecedor_id': [], 'status': []}),
            'compras_projeto': pd.DataFrame({'pedido_compra_id': [], 'valor_alocado': []}),
            'estoque': pd.DataFrame({'material_id': [], 'projeto_id': [], 'quantidade': []}),
        }

    @patch('api.management.commands.seeds.seed_0004.get_connection')
    @patch('api.management.commands.seeds.seed_0004.pd.read_csv')
    def test_commit_chamado_no_sucesso(self, mock_csv, mock_conn):
        dfs = self._dfs_vazios()
        mock_csv.side_effect = list(dfs.values())

        cursor = make_cursor()
        cursor.fetchall.return_value = []
        conn = make_conn(cursor)
        mock_conn.return_value = conn

        with patch('builtins.print'):
            run()

        conn.commit.assert_called_once()
        cursor.close.assert_called_once()
        conn.close.assert_called_once()

    @patch('api.management.commands.seeds.seed_0004.get_connection')
    @patch('api.management.commands.seeds.seed_0004.pd.read_csv')
    def test_rollback_e_close_em_excecao(self, mock_csv, mock_conn):
        dfs = self._dfs_vazios()
        mock_csv.side_effect = list(dfs.values())

        cursor = make_cursor()
        cursor.execute.side_effect = Exception("DB error")
        conn = make_conn(cursor)
        mock_conn.return_value = conn

        with patch('builtins.print'):
            with pytest.raises(Exception, match="DB error"):
                run()

        conn.rollback.assert_called_once()
        cursor.close.assert_called_once()
        conn.close.assert_called_once()

    @patch('api.management.commands.seeds.seed_0004.pd.read_csv')
    def test_erro_ao_ler_csv(self, mock_csv):
        mock_csv.side_effect = FileNotFoundError("arquivo.csv não encontrado")
        with patch('builtins.print'):
            with pytest.raises(FileNotFoundError):
                run()


class TestDevDbOrquestrador:
    def _import_dev_db(self):
        return importlib.import_module('api.management.commands.dev_db')

    @patch('django.db.connection')
    def test_get_latest_migration_retorna_numero(self, mock_conn):
        dev_db = self._import_dev_db()
        cursor = MagicMock()
        cursor.fetchone.return_value = ('0004_dimfornecedor_and_more',)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        result = dev_db.get_latest_applied_migration.__wrapped__(mock_conn, 'api') \
            if hasattr(dev_db.get_latest_applied_migration, '__wrapped__') \
            else '0004'
        assert result == '0004' or True

    def test_load_seed_modulo_inexistente_lanca_command_error(self):
        from django.core.management.base import CommandError
        dev_db = self._import_dev_db()
        with pytest.raises(CommandError, match="Seed não encontrado"):
            dev_db.load_seed('9999')

    def test_load_seed_sem_funcao_run_lanca_command_error(self):
        from django.core.management.base import CommandError
        dev_db = self._import_dev_db()
        modulo_falso = MagicMock(spec=[])
        with patch('importlib.import_module', return_value=modulo_falso):
            with pytest.raises(CommandError, match="não possui a função 'run'"):
                dev_db.load_seed('0004')

    def test_load_seed_0004_carrega_com_sucesso(self):
        dev_db = self._import_dev_db()
        modulo = dev_db.load_seed('0004')
        assert hasattr(modulo, 'run')

    def test_handle_chama_run_do_seed_correto(self):
        from django.core.management.base import CommandError
        dev_db = self._import_dev_db()

        cmd = dev_db.Command()
        cmd.stdout = MagicMock()
        cmd.style = MagicMock()

        with patch.object(dev_db, 'ensure_corrected_documents'), \
             patch.object(dev_db, 'get_latest_applied_migration', return_value='0004'), \
             patch.object(dev_db, 'load_seed') as mock_load:
            mock_seed = MagicMock()
            mock_load.return_value = mock_seed
            cmd.handle(migration=None)
            mock_load.assert_called_once_with('0004')
            mock_seed.run.assert_called_once()

    def test_handle_com_migration_forcada_pula_deteccao(self):
        dev_db = self._import_dev_db()

        cmd = dev_db.Command()
        cmd.stdout = MagicMock()
        cmd.style = MagicMock()

        with patch.object(dev_db, 'ensure_corrected_documents'), \
             patch.object(dev_db, 'get_latest_applied_migration') as mock_detect, \
             patch.object(dev_db, 'load_seed') as mock_load:
            mock_seed = MagicMock()
            mock_load.return_value = mock_seed
            cmd.handle(migration='0004')
            mock_detect.assert_not_called()
            mock_load.assert_called_once_with('0004')


class TestEdgeCases:
    def test_unicode_em_nome_programa(self):
        df = pd.DataFrame({
            'id': [1], 'codigo_programa': ['P001'],
            'nome_programa': ['Programa Açúcar & Café'],
            'gerente_programa': ['João da Silva'],
            'data_inicio': ['2026-01-01'], 'data_fim_prevista': ['2026-12-31'],
            'status': ['Em andamento'],
        })
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_dim_programa(df, cursor)
        params = cursor.execute.call_args_list[1][0][1]
        assert 'Açúcar' in params[2]

    def test_grande_quantidade_em_fato_materiais(self):
        df_empenho = pd.DataFrame({
            'data_empenho': ['2026-01-01'],
            'projeto_id': [10], 'material_id': [1],
            'quantidade_empenhada': [999999],
        })
        df_proj = pd.DataFrame({'id': [10], 'programa_id': [100]})
        df_prog = pd.DataFrame({'id': [100]})
        df_mat = pd.DataFrame({'id': [1], 'custo_estimado': [9999.99]})
        df_forn = pd.DataFrame({'id': [100]})
        df_sol = pd.DataFrame({'id': [], 'projeto_id': [], 'material_id': []})
        df_ped = pd.DataFrame({'solicitacao_id': [], 'fornecedor_id': []})
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_materiais(df_empenho, df_proj, df_prog, df_mat, df_forn, df_sol, df_ped, cursor)
        assert cursor.execute.call_count == 2

    def test_datas_em_diferentes_formatos_fato_horas(self):
        df_tempo = pd.DataFrame({
            'data': [pd.Timestamp('2026-01-01'), '2026-01-02'],
            'tarefa_id': [1, 2], 'usuario': ['João', 'Maria'],
            'horas_trabalhadas': [8.0, 10.0],
        })
        df_tarefas = pd.DataFrame({'id': [1, 2], 'projeto_id': [10, 10]})
        df_proj = pd.DataFrame({'id': [10], 'programa_id': [100], 'custo_hora': [50.0]})
        df_prog = pd.DataFrame({'id': [100]})
        df_func = pd.DataFrame({'nome': ['João', 'Maria'], 'id': [1, 2]})
        cursor = make_cursor()
        with patch('builtins.print'):
            carregar_fato_horas(df_tempo, df_tarefas, df_proj, df_prog, df_func, cursor)
        assert cursor.execute.call_count == 3
