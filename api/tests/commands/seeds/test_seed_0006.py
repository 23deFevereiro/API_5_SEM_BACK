# Fora da especificação de testes de integração: testes de seed de dados
# (infraestrutura).
import os
import sys
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "management", "commands", "seeds"
    ),
)

from seed_0006 import MIGRATION_REF, carregar_dim_projeto, run


def make_cursor():
    return MagicMock()


class TestMigrationRef:
    def test_migration_ref_is_0006(self):
        assert MIGRATION_REF == "0006"


class TestCarregarDimProjetoCom0006:
    """Testa a função local carregar_dim_projeto do seed_0006, que inclui
    data_inicio e data_fim_prevista."""

    @patch("builtins.print")
    def test_truncates_and_inserts_com_datas(self, mock_print):
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
                "data_inicio": ["2022-01-01"],
                "data_fim_prevista": ["2023-12-31"],
            }
        )
        carregar_dim_projeto(df, cursor)
        assert cursor.execute.call_count == 2
        mock_print.assert_called_once()

    @patch("builtins.print")
    def test_insere_data_inicio_e_data_fim_nos_args(self, mock_print):
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
                "data_inicio": ["2022-03-15"],
                "data_fim_prevista": ["2023-06-30"],
            }
        )
        carregar_dim_projeto(df, cursor)
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[7] == "2022-03-15"
        assert insert_args[8] == "2023-06-30"

    @patch("builtins.print")
    def test_converte_nan_para_none_em_data_inicio(self, mock_print):
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
                "data_inicio": [float("nan")],
                "data_fim_prevista": ["2023-06-30"],
            }
        )
        carregar_dim_projeto(df, cursor)
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[7] is None

    @patch("builtins.print")
    def test_converte_nan_para_none_em_data_fim_prevista(self, mock_print):
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
                "data_inicio": ["2022-03-15"],
                "data_fim_prevista": [float("nan")],
            }
        )
        carregar_dim_projeto(df, cursor)
        insert_args = cursor.execute.call_args_list[1][0][1]
        assert insert_args[8] is None

    @patch("builtins.print")
    def test_insere_multiplas_linhas(self, mock_print):
        cursor = make_cursor()
        df = pd.DataFrame(
            {
                "id": [1, 2],
                "codigo_projeto": ["PR001", "PR002"],
                "nome_projeto": ["Projeto A", "Projeto B"],
                "programa_id": [1, 1],
                "responsavel": ["Resp A", "Resp B"],
                "custo_hora": [100.0, 80.0],
                "status": ["Ativo", "Ativo"],
                "data_inicio": ["2022-01-01", "2022-06-01"],
                "data_fim_prevista": ["2023-12-31", float("nan")],
            }
        )
        carregar_dim_projeto(df, cursor)
        assert cursor.execute.call_count == 3


class TestRun0006:
    """Testa que run() do seed_0006 delega para _run_base (seed_0005.run)
    passando a fn local."""

    @patch("builtins.print")
    @patch("seed_0006._run_base")
    def test_run_delega_para_run_base(self, mock_run_base, mock_print):
        run()
        mock_run_base.assert_called_once()

    @patch("builtins.print")
    @patch("seed_0006._run_base")
    def test_run_passa_carregar_dim_projeto_como_argumento(
        self, mock_run_base, mock_print
    ):
        run()
        _, kwargs = mock_run_base.call_args
        assert kwargs.get("carregar_projeto_fn") is carregar_dim_projeto


class TestCommand0006:
    @patch("api.management.commands.seeds.seed_0006.run")
    def test_handle_calls_run(self, mock_run):
        from api.management.commands.seeds.seed_0006 import Command as Cmd

        cmd = Cmd()
        cmd.handle()
        mock_run.assert_called_once()

    def test_help_text_contains_migration_ref(self):
        from api.management.commands.seeds.seed_0006 import Command as Cmd

        cmd = Cmd()
        assert "0006" in cmd.help
