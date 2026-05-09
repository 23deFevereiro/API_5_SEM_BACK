import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'management', 'commands', 'seeds'))

from seed_0005 import (
    run,
    carregar_dim_projeto,
    MIGRATION_REF,
)
from seed_0004 import Command


def make_cursor():
    return MagicMock()


class TestMigrationRef:
    def test_migration_ref_is_0005(self):
        assert MIGRATION_REF == '0005'


class TestCarregarDimProjetoPadrao:
    """Testa a função carregar_dim_projeto do seed_0005 (sem data_inicio/data_fim_prevista)."""

    @patch('builtins.print')
    def test_truncates_and_inserts_sem_datas_extras(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame({
            'id': [1],
            'codigo_projeto': ['PR001'],
            'nome_projeto': ['Projeto A'],
            'programa_id': [1],
            'responsavel': ['Resp A'],
            'custo_hora': [100.0],
            'status': ['Ativo'],
        })
        carregar_dim_projeto(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch('builtins.print')
    def test_insere_multiplas_linhas(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame({
            'id': [1, 2],
            'codigo_projeto': ['PR001', 'PR002'],
            'nome_projeto': ['Projeto A', 'Projeto B'],
            'programa_id': [1, 1],
            'responsavel': ['Resp A', 'Resp B'],
            'custo_hora': [100.0, 80.0],
            'status': ['Ativo', 'Ativo'],
        })
        carregar_dim_projeto(df, cursor)
        assert cursor.execute.call_count == 3


class TestRun:
    """Testa o run() do seed_0005 com e sem carregar_projeto_fn personalizado."""

    def _make_mock_df(self, columns):
        return pd.DataFrame({col: [] for col in columns})

    def _patch_read_csv(self, mock_read_csv):
        """Configura side_effect do read_csv para retornar DataFrames vazios com colunas mínimas."""
        _frames = {
            'programas': pd.DataFrame({
                'id': [], 'codigo_programa': [], 'nome_programa': [],
                'gerente_programa': [], 'data_inicio': [], 'data_fim_prevista': [], 'status': [],
            }),
            'projetos': pd.DataFrame({
                'id': [], 'codigo_projeto': [], 'nome_projeto': [],
                'programa_id': [], 'responsavel': [], 'custo_hora': [], 'status': [],
            }),
            'tempo_tarefas': pd.DataFrame({'usuario': [], 'tarefa_id': [], 'horas_trabalhadas': [], 'data': []}),
            'tarefas': pd.DataFrame({
                'id': [], 'codigo_tarefa': [], 'projeto_id': [],
                'titulo': [], 'responsavel': [], 'estimativa_horas': [], 'status': [],
            }),
            'fornecedores': pd.DataFrame({
                'id': [], 'codigo_fornecedor': [], 'razao_social': [],
                'cidade': [], 'estado': [], 'categoria': [], 'status': [],
            }),
            'empenho': pd.DataFrame({'projeto_id': [], 'material_id': [], 'quantidade_empenhada': [], 'data_empenho': []}),
            'estoque': pd.DataFrame({'material_id': [], 'projeto_id': [], 'quantidade': []}),
            'materiais': pd.DataFrame({
                'id': [], 'codigo_material': [], 'descricao': [],
                'categoria': [], 'fabricante': [], 'custo_estimado': [], 'status': [],
            }),
            'solicitacoes': pd.DataFrame({'id': [], 'projeto_id': [], 'material_id': [], 'data_solicitacao': [], 'quantidade': [], 'status': []}),
            'compras_projeto': pd.DataFrame({'pedido_compra_id': [], 'valor_alocado': []}),
            'pedidos': pd.DataFrame({'solicitacao_id': [], 'id': [], 'fornecedor_id': [], 'data_pedido': [], 'data_previsao_entrega': [], 'status': [], 'valor_total': []}),
        }

        def side_effect(path):
            path_str = str(path)
            for key, df in _frames.items():
                if key in path_str:
                    return df
            return pd.DataFrame()

        mock_read_csv.side_effect = side_effect

    @patch('builtins.print')
    @patch('seed_0005.pd.read_csv')
    @patch('seed_0005.get_connection')
    def test_run_usa_carregar_dim_projeto_padrao_quando_fn_nao_passada(
        self, mock_conn, mock_read_csv, mock_print
    ):
        self._patch_read_csv(mock_read_csv)
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
        conn = MagicMock()
        conn.cursor.return_value = mock_cursor
        mock_conn.return_value = conn

        with patch('seed_0005.carregar_dim_projeto') as mock_carregar:
            run()
            mock_carregar.assert_called_once()

    @patch('builtins.print')
    @patch('seed_0005.pd.read_csv')
    @patch('seed_0005.get_connection')
    def test_run_usa_fn_personalizada_quando_passada(
        self, mock_conn, mock_read_csv, mock_print
    ):
        self._patch_read_csv(mock_read_csv)
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value = mock_cursor
        mock_conn.return_value = conn

        fn_personalizada = MagicMock()
        run(carregar_projeto_fn=fn_personalizada)

        fn_personalizada.assert_called_once()

    @patch('builtins.print')
    @patch('seed_0005.pd.read_csv')
    @patch('seed_0005.get_connection')
    def test_run_faz_commit_em_caso_de_sucesso(
        self, mock_conn, mock_read_csv, mock_print
    ):
        self._patch_read_csv(mock_read_csv)
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value = mock_cursor
        mock_conn.return_value = conn

        run(carregar_projeto_fn=MagicMock())

        conn.commit.assert_called_once()

    @patch('builtins.print')
    @patch('seed_0005.pd.read_csv')
    @patch('seed_0005.get_connection')
    def test_run_faz_rollback_e_levanta_excecao_em_caso_de_erro(
        self, mock_conn, mock_read_csv, mock_print
    ):
        self._patch_read_csv(mock_read_csv)
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        fn_que_explode = MagicMock(side_effect=RuntimeError('falha'))

        with pytest.raises(RuntimeError, match='falha'):
            run(carregar_projeto_fn=fn_que_explode)

        conn.rollback.assert_called_once()

    @patch('builtins.print')
    @patch('seed_0005.pd.read_csv')
    @patch('seed_0005.get_connection')
    def test_run_fecha_conexao_apos_execucao(
        self, mock_conn, mock_read_csv, mock_print
    ):
        self._patch_read_csv(mock_read_csv)
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value = mock_cursor
        mock_conn.return_value = conn

        run(carregar_projeto_fn=MagicMock())

        conn.close.assert_called_once()
        mock_cursor.close.assert_called_once()


class TestCommand0005:
    @patch('api.management.commands.seeds.seed_0005.run')
    def test_handle_calls_run(self, mock_run):
        from api.management.commands.seeds.seed_0005 import Command as Cmd
        cmd = Cmd()
        cmd.handle()
        mock_run.assert_called_once()
