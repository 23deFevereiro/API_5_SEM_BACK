import os
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "management", "commands", "seeds"
    ),
)

from seed_0003 import (
    DB_CONFIG,
    MIGRATION_REF,
    Command,
    _none,
    carregar_compras_projeto,
    carregar_empenho_material,
    carregar_estoque_material_projeto,
    carregar_fornecedor,
    carregar_material,
    carregar_pedido_compra,
    carregar_programa,
    carregar_projeto,
    carregar_solicitacao_compra,
    carregar_tarefa,
    carregar_tempo_tarefa,
    get_connection,
    run,
)


def make_cursor():
    return MagicMock()


class TestNone:
    def test_returns_none_for_nan(self):
        assert _none(float("nan")) is None

    def test_returns_none_for_pd_na(self):
        assert _none(pd.NA) is None

    def test_returns_none_for_np_nan(self):
        assert _none(np.nan) is None

    def test_returns_none_for_none_via_pd_isna(self):
        assert _none(None) is None

    def test_returns_value_for_string(self):
        assert _none("hello") == "hello"

    def test_returns_value_for_int(self):
        assert _none(42) == 42

    def test_returns_value_for_zero(self):
        assert _none(0) == 0

    def test_returns_value_for_false(self):
        assert _none(False) is False

    def test_returns_value_for_list_typeerror_path(self):
        val = [1, 2]
        assert _none(val) == val

    def test_numpy_scalar_returns_item(self):
        val = np.int64(7)
        result = _none(val)
        assert result == 7
        assert isinstance(result, int)


class TestGetConnection:
    @patch("seed_0003.psycopg2.connect")
    def test_calls_connect_with_db_config(self, mock_connect):
        get_connection()
        mock_connect.assert_called_once_with(**DB_CONFIG)


class TestConstants:
    def test_migration_ref(self):
        assert MIGRATION_REF == "0003"


class TestCarregarPrograma:
    @patch("builtins.print")
    def test_truncates_and_inserts(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_programa": ["P001"],
                "nome_programa": ["Programa A"],
                "gerente_programa": ["Gerente 1"],
                "gerente_tecnico": ["Tecnico 1"],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": ["2023-12-31"],
                "status": ["Ativo"],
            }
        )
        carregar_programa(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_handles_nan_gerente_and_data_fim(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_programa": ["P001"],
                "nome_programa": ["Programa A"],
                "gerente_programa": [float("nan")],
                "gerente_tecnico": [float("nan")],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": [float("nan")],
                "status": ["Ativo"],
            }
        )
        carregar_programa(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[3] is None
        assert args[4] is None
        assert args[6] is None

    @patch("builtins.print")
    def test_missing_gerente_tecnico_column_defaults_empty(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_programa": ["P001"],
                "nome_programa": ["Programa A"],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": ["2023-12-31"],
                "status": ["Ativo"],
            }
        )
        carregar_programa(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[3] is None
        assert args[4] == ""

    @patch("builtins.print")
    def test_multiple_rows(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1, 2],
                "codigo_programa": ["P001", "P002"],
                "nome_programa": ["Prog A", "Prog B"],
                "gerente_programa": ["G1", "G2"],
                "gerente_tecnico": ["T1", "T2"],
                "data_inicio": ["2022-01-01", "2022-06-01"],
                "data_fim_prevista": ["2023-12-31", "2024-06-30"],
                "status": ["Ativo", "Ativo"],
            }
        )
        carregar_programa(df, cursor)
        assert cursor.execute.call_count == 3


class TestCarregarProjeto:
    @patch("builtins.print")
    def test_truncates_and_inserts(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_projeto": ["PR001"],
                "nome_projeto": ["Projeto A"],
                "programa_id": [1],
                "responsavel": ["Resp A"],
                "custo_hora": [100.0],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": ["2023-12-31"],
                "status": ["Ativo"],
            }
        )
        carregar_projeto(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_handles_nan_custo_and_data_fim(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_projeto": ["PR001"],
                "nome_projeto": ["Projeto A"],
                "programa_id": [float("nan")],
                "responsavel": ["Resp"],
                "custo_hora": [float("nan")],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": [float("nan")],
                "status": ["Ativo"],
            }
        )
        carregar_projeto(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[3] is None
        assert args[5] is None
        assert args[7] is None


class TestCarregarTarefa:
    @patch("builtins.print")
    def test_truncates_and_inserts(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_tarefa": ["T001"],
                "projeto_id": [1],
                "titulo": ["Tarefa 1"],
                "responsavel": ["Resp"],
                "estimativa_horas": [8.0],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": ["2022-06-30"],
                "status": ["Aberta"],
            }
        )
        carregar_tarefa(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_handles_nan_estimativa_and_data_fim(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_tarefa": ["T001"],
                "projeto_id": [float("nan")],
                "titulo": ["Tarefa 1"],
                "responsavel": ["Resp"],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": [float("nan")],
                "status": ["Aberta"],
            }
        )
        carregar_tarefa(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[2] is None
        assert args[5] is None
        assert args[7] is None


class TestCarregarTempoTarefa:
    @patch("builtins.print")
    def test_inserts_valid_horas(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "tarefa_id": [1],
                "usuario": ["Alice"],
                "data": ["2023-04-01"],
                "horas_trabalhadas": [6.0],
            }
        )
        carregar_tempo_tarefa(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_skips_nan_horas(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "tarefa_id": [1],
                "usuario": ["Alice"],
                "data": ["2023-04-01"],
                "horas_trabalhadas": [float("nan")],
            }
        )
        carregar_tempo_tarefa(df, cursor)
        assert cursor.execute.call_count == 1
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_skips_none_horas(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "tarefa_id": [1],
                "usuario": ["Alice"],
                "data": ["2023-04-01"],
                "horas_trabalhadas": [None],
            }
        )
        carregar_tempo_tarefa(df, cursor)
        assert cursor.execute.call_count == 1

    @patch("builtins.print")
    def test_multiple_rows_mixed(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "tarefa_id": [1, 2, 3],
                "usuario": ["Alice", "Bob", "Carol"],
                "data": ["2023-04-01", "2023-04-02", "2023-04-03"],
                "horas_trabalhadas": [4.0, float("nan"), 8.0],
            }
        )
        carregar_tempo_tarefa(df, cursor)
        assert cursor.execute.call_count == 3
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_insert_args_cast(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "tarefa_id": [2],
                "usuario": ["Bob"],
                "data": ["2023-05-10"],
                "horas_trabalhadas": [3.5],
            }
        )
        carregar_tempo_tarefa(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[0] == 2
        assert args[1] == "Bob"
        assert args[2] == "2023-05-10"
        assert args[3] == pytest.approx(3.5)


class TestCarregarFornecedor:
    @patch("builtins.print")
    def test_truncates_and_inserts(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_fornecedor": ["F001"],
                "razao_social": ["Empresa A"],
                "cidade": ["São Paulo"],
                "estado": ["SP"],
                "categoria": ["Cat A"],
                "status": ["Ativo"],
            }
        )
        carregar_fornecedor(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_handles_nan_id(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [float("nan")],
                "codigo_fornecedor": ["F001"],
                "razao_social": ["Empresa A"],
                "cidade": ["SP"],
                "estado": ["SP"],
                "categoria": ["Cat A"],
                "status": ["Ativo"],
            }
        )
        carregar_fornecedor(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[0] is None


class TestCarregarMaterial:
    @patch("builtins.print")
    def test_truncates_and_inserts(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_material": ["M001"],
                "descricao": ["Material X"],
                "categoria": ["Cat A"],
                "fabricante": ["Fab A"],
                "custo_estimado": [50.0],
                "status": ["Ativo"],
            }
        )
        carregar_material(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_handles_nan_custo(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_material": ["M001"],
                "descricao": ["Material X"],
                "categoria": ["Cat A"],
                "fabricante": ["Fab A"],
                "custo_estimado": [float("nan")],
                "status": ["Ativo"],
            }
        )
        carregar_material(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[5] is None


class TestCarregarPedidoCompra:
    @patch("builtins.print")
    def test_truncates_and_inserts(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "numero_pedido": ["PC001"],
                "fornecedor_id": [1],
                "data_pedido": ["2023-01-01"],
                "data_previsao_entrega": ["2023-01-15"],
                "valor_total": [500.0],
                "status": ["Aberto"],
            }
        )
        carregar_pedido_compra(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_handles_nan_data_previsao_and_valor(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [float("nan")],
                "numero_pedido": ["PC001"],
                "fornecedor_id": [1],
                "data_pedido": ["2023-01-01"],
                "data_previsao_entrega": [float("nan")],
                "valor_total": [float("nan")],
                "status": ["Aberto"],
            }
        )
        carregar_pedido_compra(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[0] is None
        assert args[4] is None
        assert args[5] is None


class TestCarregarComprasProjeto:
    @patch("builtins.print")
    def test_truncates_and_inserts(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "pedido_compra_id": [1],
                "projeto_id": [1],
                "valor_alocado": [200.0],
            }
        )
        carregar_compras_projeto(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_insert_args_cast(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [3],
                "pedido_compra_id": [5],
                "projeto_id": [2],
                "valor_alocado": [150.75],
            }
        )
        carregar_compras_projeto(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[0] == 3
        assert args[1] == 5
        assert args[2] == 2
        assert args[3] == pytest.approx(150.75)


class TestCarregarSolicitacaoCompra:
    @patch("builtins.print")
    def test_truncates_and_inserts(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "numero_solicitacao": ["SC001"],
                "projeto_id": [1],
                "material_id": [1],
                "quantidade": [10],
                "data_solicitacao": ["2023-02-01"],
                "prioridade": ["Alta"],
                "status": ["Aberto"],
            }
        )
        carregar_solicitacao_compra(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_insert_args_cast(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [7],
                "numero_solicitacao": ["SC007"],
                "projeto_id": [2],
                "material_id": [3],
                "quantidade": [5],
                "data_solicitacao": ["2023-03-15"],
                "prioridade": ["Baixa"],
                "status": ["Pendente"],
            }
        )
        carregar_solicitacao_compra(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[0] == 7
        assert args[2] == 2
        assert args[3] == 3
        assert args[4] == 5


class TestCarregarEmpenhoMaterial:
    @patch("builtins.print")
    def test_truncates_and_inserts(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "projeto_id": [1],
                "material_id": [1],
                "quantidade_empenhada": [3],
                "data_empenho": ["2023-05-01"],
            }
        )
        carregar_empenho_material(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_insert_args_cast(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "projeto_id": [2],
                "material_id": [4],
                "quantidade_empenhada": [7],
                "data_empenho": ["2023-06-15"],
            }
        )
        carregar_empenho_material(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[0] == 2
        assert args[1] == 4
        assert args[2] == 7
        assert args[3] == "2023-06-15"

    @patch("builtins.print")
    def test_multiple_rows(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "projeto_id": [1, 2],
                "material_id": [1, 2],
                "quantidade_empenhada": [5, 10],
                "data_empenho": ["2023-05-01", "2023-05-02"],
            }
        )
        carregar_empenho_material(df, cursor)
        assert cursor.execute.call_count == 3


class TestCarregarEstoqueMaterialProjeto:
    @patch("builtins.print")
    def test_truncates_and_inserts_with_localizacao(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "projeto_id": [1],
                "material_id": [1],
                "quantidade": [20],
                "localizacao": ["Prateleira A"],
            }
        )
        carregar_estoque_material_projeto(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()
        args = cursor.execute.call_args_list[1][0][1]
        assert args[3] == "Prateleira A"

    @patch("builtins.print")
    def test_defaults_localizacao_to_na_when_absent(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "projeto_id": [1],
                "material_id": [2],
                "quantidade": [5],
            }
        )
        carregar_estoque_material_projeto(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[3] == "N/A"

    @patch("builtins.print")
    def test_multiple_rows(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "projeto_id": [1, 2],
                "material_id": [1, 3],
                "quantidade": [10, 30],
                "localizacao": ["Dep A", "Dep B"],
            }
        )
        carregar_estoque_material_projeto(df, cursor)
        assert cursor.execute.call_count == 3

    @patch("builtins.print")
    def test_insert_args_cast(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "projeto_id": [3],
                "material_id": [5],
                "quantidade": [12],
                "localizacao": ["Galpão 1"],
            }
        )
        carregar_estoque_material_projeto(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[0] == 3
        assert args[1] == 5
        assert args[2] == 12


class TestRun:
    def _make_conn_mock(self, cursor_mock):
        conn = MagicMock()
        conn.cursor.return_value = cursor_mock
        return conn

    def _patch_read_csv(self):
        df_programas = pd.DataFrame(
            {
                "id": [1],
                "codigo_programa": ["P001"],
                "nome_programa": ["Prog"],
                "gerente_programa": ["G"],
                "gerente_tecnico": ["T"],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": ["2023-12-31"],
                "status": ["Ativo"],
            }
        )
        df_projetos = pd.DataFrame(
            {
                "id": [1],
                "codigo_projeto": ["PR001"],
                "nome_projeto": ["Proj"],
                "programa_id": [1],
                "responsavel": ["R"],
                "custo_hora": [50.0],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": ["2023-12-31"],
                "status": ["Ativo"],
            }
        )
        df_tarefas = pd.DataFrame(
            {
                "id": [1],
                "codigo_tarefa": ["T001"],
                "projeto_id": [1],
                "titulo": ["Tar"],
                "responsavel": ["R"],
                "estimativa_horas": [8.0],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": ["2022-06-30"],
                "status": ["Aberta"],
            }
        )
        df_materiais = pd.DataFrame(
            {
                "id": [1],
                "codigo_material": ["M001"],
                "descricao": ["Mat"],
                "categoria": ["C"],
                "fabricante": ["F"],
                "custo_estimado": [10.0],
                "status": ["Ativo"],
            }
        )
        df_fornecedores = pd.DataFrame(
            {
                "id": [1],
                "codigo_fornecedor": ["F001"],
                "razao_social": ["Emp"],
                "cidade": ["SP"],
                "estado": ["SP"],
                "categoria": ["C"],
                "status": ["Ativo"],
            }
        )
        df_tempo_tarefas = pd.DataFrame(
            {
                "tarefa_id": [1],
                "usuario": ["Alice"],
                "horas_trabalhadas": [4.0],
                "data": ["2023-06-01"],
            }
        )
        df_empenho = pd.DataFrame(
            {
                "projeto_id": [1],
                "material_id": [1],
                "quantidade_empenhada": [2],
                "data_empenho": ["2023-06-01"],
            }
        )
        df_solicitacoes = pd.DataFrame(
            {
                "id": [1],
                "numero_solicitacao": ["SC001"],
                "projeto_id": [1],
                "material_id": [1],
                "quantidade": [2],
                "data_solicitacao": ["2023-06-01"],
                "prioridade": ["Alta"],
                "status": ["Aberto"],
            }
        )
        df_pedidos = pd.DataFrame(
            {
                "id": [1],
                "numero_pedido": ["PC001"],
                "fornecedor_id": [1],
                "data_pedido": ["2023-06-01"],
                "data_previsao_entrega": ["2023-06-15"],
                "valor_total": [100.0],
                "status": ["Entregue"],
            }
        )
        df_compras_projeto = pd.DataFrame(
            {
                "id": [1],
                "pedido_compra_id": [1],
                "projeto_id": [1],
                "valor_alocado": [100.0],
            }
        )
        df_estoque = pd.DataFrame(
            {
                "projeto_id": [1],
                "material_id": [1],
                "quantidade": [5],
                "localizacao": ["Dep A"],
            }
        )
        return [
            df_programas,
            df_projetos,
            df_tarefas,
            df_materiais,
            df_fornecedores,
            df_tempo_tarefas,
            df_empenho,
            df_solicitacoes,
            df_pedidos,
            df_compras_projeto,
            df_estoque,
        ]

    @patch("builtins.print")
    def test_run_success(self, mock_print):
        cursor = make_cursor()
        conn = self._make_conn_mock(cursor)
        csv_data = self._patch_read_csv()

        with patch("seed_0003.get_connection", return_value=conn), patch(
            "seed_0003.pd.read_csv", side_effect=csv_data
        ):
            run()

        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()
        cursor.close.assert_called_once()
        conn.close.assert_called_once()

    @patch("builtins.print")
    def test_run_rollback_on_exception(self, mock_print):
        cursor = MagicMock()
        cursor.execute.side_effect = Exception("DB error")
        conn = self._make_conn_mock(cursor)
        csv_data = self._patch_read_csv()

        with patch("seed_0003.get_connection", return_value=conn), patch(
            "seed_0003.pd.read_csv", side_effect=csv_data
        ):
            with pytest.raises(Exception, match="DB error"):
                run()

        conn.rollback.assert_called_once()
        cursor.close.assert_called_once()
        conn.close.assert_called_once()


class TestCommand:
    @patch("seed_0003.run")
    def test_handle_calls_run(self, mock_run):
        cmd = Command()
        cmd.handle()
        mock_run.assert_called_once()

    def test_help_text(self):
        cmd = Command()
        assert "0003" in cmd.help
