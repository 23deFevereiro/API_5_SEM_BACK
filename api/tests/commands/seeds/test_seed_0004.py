import os
import sys
from datetime import date, datetime
from unittest.mock import MagicMock, call, patch

import numpy as np
import pandas as pd
import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "management", "commands", "seeds"
    ),
)

from seed_0004 import MIGRATION_REF, Command, run
from seed_0005 import (
    DB_CONFIG,
    _none,
    carregar_dim_fornecedor,
    carregar_dim_funcionario,
    carregar_dim_material,
    carregar_dim_programa,
    carregar_dim_projeto,
    carregar_dim_status_pedido,
    carregar_dim_tarefa,
    carregar_dim_tempo,
    carregar_fato_compras,
    carregar_fato_estoque,
    carregar_fato_horas,
    carregar_fato_materiais,
    get_connection,
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

    def test_returns_value_for_string(self):
        assert _none("hello") == "hello"

    def test_returns_value_for_int(self):
        assert _none(42) == 42

    def test_returns_value_for_zero(self):
        assert _none(0) == 0

    def test_returns_value_for_false(self):
        assert _none(False) is False

    def test_returns_none_for_none_via_pd_isna(self):
        assert _none(None) is None

    def test_returns_value_for_list_typeerror_path(self):
        val = [1, 2]
        assert _none(val) == val


class TestGetConnection:
    @patch("seed_0005.psycopg2.connect")
    def test_calls_connect_with_db_config(self, mock_connect):
        get_connection()
        mock_connect.assert_called_once_with(**DB_CONFIG)


class TestConstants:
    def test_migration_ref(self):
        assert MIGRATION_REF == "0004"


class TestCarregarDimPrograma:
    @patch("builtins.print")
    def test_truncates_and_inserts(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_programa": ["P001"],
                "nome_programa": ["Programa A"],
                "gerente_programa": ["Gerente 1"],
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": ["2023-12-31"],
                "status": ["Ativo"],
            }
        )
        carregar_dim_programa(df, cursor)
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
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": [float("nan")],
                "status": ["Ativo"],
            }
        )
        carregar_dim_programa(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[3] is None
        assert args[5] is None


class TestCarregarDimProjeto:
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
                "status": ["Ativo"],
            }
        )
        carregar_dim_projeto(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()


class TestCarregarDimTarefa:
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
                "status": ["Aberta"],
            }
        )
        carregar_dim_tarefa(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_handles_nan_estimativa(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1],
                "codigo_tarefa": ["T001"],
                "projeto_id": [1],
                "titulo": ["Tarefa 1"],
                "responsavel": ["Resp"],
                "estimativa_horas": [float("nan")],
                "status": ["Aberta"],
            }
        )
        carregar_dim_tarefa(df, cursor)
        args = cursor.execute.call_args_list[1][0][1]
        assert args[5] is None


class TestCarregarDimMaterial:
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
        carregar_dim_material(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()


class TestCarregarDimFornecedor:
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
        carregar_dim_fornecedor(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()


class TestCarregarDimFuncionario:
    @patch("builtins.print")
    def test_inserts_unique_names(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame({"usuario": ["Alice", "Bob", "Alice"]})
        carregar_dim_funcionario(df, cursor)
        assert cursor.execute.call_count == 3
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_drops_nan_users(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame({"usuario": ["Alice", float("nan"), "Bob"]})
        carregar_dim_funcionario(df, cursor)
        assert cursor.execute.call_count == 3
        mock_print.assert_called_once()


class TestCarregarDimStatusPedido:
    @patch("builtins.print")
    def test_inserts_five_statuses(self, mock_print):
        cursor = make_cursor()
        carregar_dim_status_pedido(cursor)
        assert cursor.execute.call_count == 6
        mock_print.assert_called_once()


class TestCarregarDimTempo:
    @patch("builtins.print")
    def test_inserts_records_for_date_range(self, mock_print):
        cursor = make_cursor()
        carregar_dim_tempo(cursor)
        expected_days = (datetime(2026, 12, 31) - datetime(2022, 1, 1)).days + 1
        assert cursor.execute.call_count == 1 + expected_days
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_semestre_calculation(self, mock_print):
        cursor = make_cursor()
        carregar_dim_tempo(cursor)
        calls = cursor.execute.call_args_list
        jan_call = next(c for c in calls[1:] if c[0][1][2] == 2022 and c[0][1][3] == 1)
        assert jan_call[0][1][5] == 1
        jul_call = next(c for c in calls[1:] if c[0][1][2] == 2022 and c[0][1][3] == 7)
        assert jul_call[0][1][5] == 2

    @patch("builtins.print")
    def test_tempo_id_format(self, mock_print):
        cursor = make_cursor()
        carregar_dim_tempo(cursor)
        calls = cursor.execute.call_args_list
        first_insert = calls[1][0][1]
        assert first_insert[0] == 20220101


class TestCarregarFatoHoras:
    def _make_dfs(self):
        df_projetos = pd.DataFrame(
            {"id": [1], "programa_id": [10], "custo_hora": [50.0]}
        )
        df_tarefas = pd.DataFrame({"id": [1], "projeto_id": [1]})
        df_programas = pd.DataFrame({"id": [10]})
        df_funcionario = pd.DataFrame({"id": [1], "nome": ["Alice"]})
        df_tempo = pd.DataFrame(
            {
                "tarefa_id": [1],
                "usuario": ["Alice"],
                "horas_trabalhadas": [8.0],
                "data": ["2023-03-15"],
            }
        )
        return df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario

    @patch("builtins.print")
    def test_inserts_record(self, mock_print):
        cursor = make_cursor()
        df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario = (
            self._make_dfs()
        )
        carregar_fato_horas(
            df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor
        )
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_skips_nan_horas(self, mock_print):
        cursor = make_cursor()
        df_projetos = pd.DataFrame(
            {"id": [1], "programa_id": [10], "custo_hora": [50.0]}
        )
        df_tarefas = pd.DataFrame({"id": [1], "projeto_id": [1]})
        df_programas = pd.DataFrame({"id": [10]})
        df_funcionario = pd.DataFrame({"id": [1], "nome": ["Alice"]})
        df_tempo = pd.DataFrame(
            {
                "tarefa_id": [1],
                "usuario": ["Alice"],
                "horas_trabalhadas": [float("nan")],
                "data": ["2023-03-15"],
            }
        )
        carregar_fato_horas(
            df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor
        )
        assert cursor.execute.call_count == 1

    @patch("builtins.print")
    def test_skips_zero_horas(self, mock_print):
        cursor = make_cursor()
        df_projetos = pd.DataFrame(
            {"id": [1], "programa_id": [10], "custo_hora": [50.0]}
        )
        df_tarefas = pd.DataFrame({"id": [1], "projeto_id": [1]})
        df_programas = pd.DataFrame({"id": [10]})
        df_funcionario = pd.DataFrame({"id": [1], "nome": ["Alice"]})
        df_tempo = pd.DataFrame(
            {
                "tarefa_id": [1],
                "usuario": ["Alice"],
                "horas_trabalhadas": [0.0],
                "data": ["2023-03-15"],
            }
        )
        carregar_fato_horas(
            df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor
        )
        assert cursor.execute.call_count == 1

    @patch("builtins.print")
    def test_skips_missing_tarefa(self, mock_print):
        cursor = make_cursor()
        df_projetos = pd.DataFrame(
            {"id": [1], "programa_id": [10], "custo_hora": [50.0]}
        )
        df_tarefas = pd.DataFrame({"id": [2], "projeto_id": [1]})
        df_programas = pd.DataFrame({"id": [10]})
        df_funcionario = pd.DataFrame({"id": [1], "nome": ["Alice"]})
        df_tempo = pd.DataFrame(
            {
                "tarefa_id": [1],
                "usuario": ["Alice"],
                "horas_trabalhadas": [5.0],
                "data": ["2023-03-15"],
            }
        )
        carregar_fato_horas(
            df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor
        )
        assert cursor.execute.call_count == 1

    @patch("builtins.print")
    def test_unknown_funcionario_defaults_to_1(self, mock_print):
        cursor = make_cursor()
        df_projetos = pd.DataFrame(
            {"id": [1], "programa_id": [10], "custo_hora": [50.0]}
        )
        df_tarefas = pd.DataFrame({"id": [1], "projeto_id": [1]})
        df_programas = pd.DataFrame({"id": [10]})
        df_funcionario = pd.DataFrame({"id": [99], "nome": ["Outro"]})
        df_tempo = pd.DataFrame(
            {
                "tarefa_id": [1],
                "usuario": ["Desconhecido"],
                "horas_trabalhadas": [4.0],
                "data": ["2023-03-15"],
            }
        )
        carregar_fato_horas(
            df_tempo, df_tarefas, df_projetos, df_programas, df_funcionario, cursor
        )
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[4] == 1


class TestCarregarFatoMateriais:
    def _make_dfs(self):
        df_projetos = pd.DataFrame({"id": [1], "programa_id": [10]})
        df_programas = pd.DataFrame({"id": [10]})
        df_materiais = pd.DataFrame({"id": [1], "custo_estimado": [20.0]})
        df_fornecedores = pd.DataFrame({"id": [1]})
        df_solicitacoes = pd.DataFrame(
            {"id": [1], "projeto_id": [1], "material_id": [1]}
        )
        df_pedidos = pd.DataFrame({"solicitacao_id": [1], "fornecedor_id": [1]})
        df_empenho = pd.DataFrame(
            {
                "projeto_id": [1],
                "material_id": [1],
                "quantidade_empenhada": [5],
                "data_empenho": ["2023-05-10"],
            }
        )
        return (
            df_empenho,
            df_projetos,
            df_programas,
            df_materiais,
            df_fornecedores,
            df_solicitacoes,
            df_pedidos,
        )

    @patch("builtins.print")
    def test_inserts_record(self, mock_print):
        cursor = make_cursor()
        args = self._make_dfs()
        carregar_fato_materiais(*args, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_fornecedor_id_none_when_no_match(self, mock_print):
        cursor = make_cursor()
        df_projetos = pd.DataFrame({"id": [1], "programa_id": [10]})
        df_programas = pd.DataFrame({"id": [10]})
        df_materiais = pd.DataFrame({"id": [2], "custo_estimado": [10.0]})
        df_fornecedores = pd.DataFrame({"id": [1]})
        df_solicitacoes = pd.DataFrame(
            {"id": [1], "projeto_id": [1], "material_id": [1]}
        )
        df_pedidos = pd.DataFrame({"solicitacao_id": [1], "fornecedor_id": [1]})
        df_empenho = pd.DataFrame(
            {
                "projeto_id": [1],
                "material_id": [2],
                "quantidade_empenhada": [3],
                "data_empenho": ["2023-05-10"],
            }
        )
        carregar_fato_materiais(
            df_empenho,
            df_projetos,
            df_programas,
            df_materiais,
            df_fornecedores,
            df_solicitacoes,
            df_pedidos,
            cursor,
        )
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[4] is None

    @patch("builtins.print")
    def test_nan_fornecedor_excluded(self, mock_print):
        cursor = make_cursor()
        df_projetos = pd.DataFrame({"id": [1], "programa_id": [10]})
        df_programas = pd.DataFrame({"id": [10]})
        df_materiais = pd.DataFrame({"id": [1], "custo_estimado": [20.0]})
        df_fornecedores = pd.DataFrame({"id": [1]})
        df_solicitacoes = pd.DataFrame(
            {"id": [1], "projeto_id": [1], "material_id": [1]}
        )
        df_pedidos = pd.DataFrame(
            {"solicitacao_id": [1], "fornecedor_id": [float("nan")]}
        )
        df_empenho = pd.DataFrame(
            {
                "projeto_id": [1],
                "material_id": [1],
                "quantidade_empenhada": [5],
                "data_empenho": ["2023-05-10"],
            }
        )
        carregar_fato_materiais(
            df_empenho,
            df_projetos,
            df_programas,
            df_materiais,
            df_fornecedores,
            df_solicitacoes,
            df_pedidos,
            cursor,
        )
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[4] is None


class TestCarregarFatoCompras:
    def _make_dfs(self, status="Entregue", with_dates=True, with_valor_alocado=True):
        df_projetos = pd.DataFrame({"id": [1], "programa_id": [10]})
        df_materiais = pd.DataFrame({"id": [1]})
        df_fornecedores = pd.DataFrame({"id": [1]})
        df_status_pedido = pd.DataFrame({"id": [4], "nome_status": [status]})
        df_solicitacoes = pd.DataFrame(
            {
                "id": [1],
                "projeto_id": [1],
                "material_id": [1],
                "data_solicitacao": ["2023-03-01"],
                "quantidade": [10],
                "status": ["Aberto"],
            }
        )
        df_pedidos = pd.DataFrame(
            {
                "solicitacao_id": [1],
                "id": [1],
                "fornecedor_id": [1],
                "data_pedido": ["2023-03-02"] if with_dates else [None],
                "data_previsao_entrega": ["2023-03-10"] if with_dates else [None],
                "status": [status],
                "valor_total": [500.0],
            }
        )
        df_compras_projeto = pd.DataFrame(
            {
                "pedido_compra_id": [1],
                "valor_alocado": [500.0] if with_valor_alocado else [float("nan")],
            }
        )
        return (
            df_solicitacoes,
            df_pedidos,
            df_compras_projeto,
            df_projetos,
            df_materiais,
            df_fornecedores,
            df_status_pedido,
        )

    @patch("builtins.print")
    def test_inserts_entregue(self, mock_print):
        cursor = make_cursor()
        args = self._make_dfs(status="Entregue")
        carregar_fato_compras(*args, cursor)
        assert cursor.execute.call_count == 2
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[5] == insert_args[6]

    @patch("builtins.print")
    def test_inserts_not_entregue(self, mock_print):
        cursor = make_cursor()
        df_status_pedido = pd.DataFrame({"id": [1], "nome_status": ["Aberto"]})
        df_solicitacoes = pd.DataFrame(
            {
                "id": [1],
                "projeto_id": [1],
                "material_id": [1],
                "data_solicitacao": ["2023-03-01"],
                "quantidade": [10],
                "status": ["Aberto"],
            }
        )
        df_pedidos = pd.DataFrame(
            {
                "solicitacao_id": [1],
                "id": [1],
                "fornecedor_id": [1],
                "data_pedido": ["2023-03-02"],
                "data_previsao_entrega": ["2023-03-10"],
                "status": ["Aberto"],
                "valor_total": [100.0],
            }
        )
        df_compras_projeto = pd.DataFrame(
            {"pedido_compra_id": [1], "valor_alocado": [100.0]}
        )
        df_projetos = pd.DataFrame({"id": [1], "programa_id": [10]})
        df_materiais = pd.DataFrame({"id": [1]})
        df_fornecedores = pd.DataFrame({"id": [1]})
        carregar_fato_compras(
            df_solicitacoes,
            df_pedidos,
            df_compras_projeto,
            df_projetos,
            df_materiais,
            df_fornecedores,
            df_status_pedido,
            cursor,
        )
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[6] == 0

    @patch("builtins.print")
    def test_lead_time_none_when_dates_missing(self, mock_print):
        cursor = make_cursor()
        args = self._make_dfs(with_dates=False)
        carregar_fato_compras(*args, cursor)
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[9] is None

    @patch("builtins.print")
    def test_lead_time_calculated(self, mock_print):
        cursor = make_cursor()
        args = self._make_dfs(with_dates=True)
        carregar_fato_compras(*args, cursor)
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[9] == 8

    @patch("builtins.print")
    def test_valor_alocado_nan_defaults_to_zero(self, mock_print):
        cursor = make_cursor()
        args = self._make_dfs(with_valor_alocado=False)
        carregar_fato_compras(*args, cursor)
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[7] == pytest.approx(0.0)

    @patch("builtins.print")
    def test_unknown_status_defaults_to_1(self, mock_print):
        cursor = make_cursor()
        df_status_pedido = pd.DataFrame({"id": [4], "nome_status": ["Entregue"]})
        df_solicitacoes = pd.DataFrame(
            {
                "id": [1],
                "projeto_id": [1],
                "material_id": [1],
                "data_solicitacao": ["2023-03-01"],
                "quantidade": [5],
                "status": ["Aberto"],
            }
        )
        df_pedidos = pd.DataFrame(
            {
                "solicitacao_id": [1],
                "id": [1],
                "fornecedor_id": [1],
                "data_pedido": [None],
                "data_previsao_entrega": [None],
                "status": ["StatusDesconhecido"],
                "valor_total": [200.0],
            }
        )
        df_compras_projeto = pd.DataFrame(
            {"pedido_compra_id": [1], "valor_alocado": [200.0]}
        )
        df_projetos = pd.DataFrame({"id": [1], "programa_id": [10]})
        df_materiais = pd.DataFrame({"id": [1]})
        df_fornecedores = pd.DataFrame({"id": [1]})
        carregar_fato_compras(
            df_solicitacoes,
            df_pedidos,
            df_compras_projeto,
            df_projetos,
            df_materiais,
            df_fornecedores,
            df_status_pedido,
            cursor,
        )
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[4] == 1


class TestCarregarFatoEstoque:
    @patch("builtins.print")
    def test_inserts_records(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "material_id": [1, 2],
                "projeto_id": [1, 1],
                "quantidade": [10, 20],
            }
        )
        carregar_fato_estoque(df, cursor)
        assert cursor.execute.call_count == 3
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_tempo_id_is_today(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "material_id": [1],
                "projeto_id": [1],
                "quantidade": [5],
            }
        )
        expected_tempo_id = int(datetime.now().date().strftime("%Y%m%d"))
        carregar_fato_estoque(df, cursor)
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[0] == expected_tempo_id


class TestRun:
    def test_delega_para_seed_0003_e_seed_0005(self):
        with patch("api.management.commands.seeds.seed_0003.run") as mock_s3_run, patch(
            "api.management.commands.seeds.seed_0005.run"
        ) as mock_s5_run, patch("builtins.print"):
            from api.management.commands.seeds.seed_0004 import run as run_0004

            run_0004()
        mock_s3_run.assert_called_once()
        mock_s5_run.assert_called_once()


class TestCommand:
    @patch("api.management.commands.seeds.seed_0004.run")
    def test_handle_calls_run(self, mock_run):
        from api.management.commands.seeds.seed_0004 import Command as Cmd0004

        cmd = Cmd0004()
        cmd.handle()
        mock_run.assert_called_once()

    def test_help_text(self):
        cmd = Command()
        assert "0004" in cmd.help
