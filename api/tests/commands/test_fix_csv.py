import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from unittest.mock import patch
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'management', 'commands'))

from fix_csv import (
    criar_pasta_saida,
    salvar_csv,
    corrigir_inconsistencia_1,
    corrigir_inconsistencia_2,
    corrigir_inconsistencia_3,
    _parsear_data_fim,
    _determinar_novo_status,
    corrigir_inconsistencia_4,
    corrigir_programas_concluidos,
    main,
    STATUS_CONCLUIDO,
    STATUS_CONCLUIDA,
)


class TestCriarPastaSaida:
    @patch('os.path.exists', return_value=False)
    @patch('os.makedirs')
    @patch('builtins.print')
    def test_criar_pasta_quando_nao_existe(self, mock_print, mock_makedirs, mock_exists):
        criar_pasta_saida()
        mock_makedirs.assert_called_once()
        assert mock_print.called

    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    def test_pasta_ja_existe(self, mock_makedirs, mock_exists):
        criar_pasta_saida()
        mock_makedirs.assert_not_called()


class TestSalvarCsv:
    @patch('builtins.print')
    def test_salvar_csv_com_sucesso(self, mock_print, tmp_path):
        df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        arquivo = tmp_path / 'test.csv'
        
        with patch('fix_csv.OUTPUT_FOLDER', str(tmp_path)):
            resultado = salvar_csv(df, 'test.csv')
        
        assert os.path.exists(resultado)
        assert mock_print.called

    def test_salvar_csv_encoding_utf8(self, tmp_path):
        df = pd.DataFrame({'nome': ['José', 'Mário'], 'status': ['Concluído', 'Em andamento']})
        
        with patch('fix_csv.OUTPUT_FOLDER', str(tmp_path)):
            caminho = salvar_csv(df, 'test_utf8.csv')
        
        df_lido = pd.read_csv(caminho, encoding='utf-8-sig')
        assert 'José' in df_lido['nome'].values


class TestCorrigirInconsistencia1:
    def test_corrigir_responsavel_simples(self):
        df_tempo = pd.DataFrame({
            'tarefa_id': [1, 2],
            'usuario': ['João', 'Maria']
        })
        df_tarefas = pd.DataFrame({
            'id': [1, 2],
            'responsavel': ['Pedro', 'Ana']
        })
        
        resultado = corrigir_inconsistencia_1(df_tempo, df_tarefas)
        
        assert resultado.loc[0, 'usuario'] == 'Pedro'
        assert resultado.loc[1, 'usuario'] == 'Ana'

    def test_sem_alteracoes_necessarias(self):
        df_tempo = pd.DataFrame({
            'tarefa_id': [1, 2],
            'usuario': ['Pedro', 'Ana']
        })
        df_tarefas = pd.DataFrame({
            'id': [1, 2],
            'responsavel': ['Pedro', 'Ana']
        })
        
        resultado = corrigir_inconsistencia_1(df_tempo, df_tarefas)
        
        assert resultado.loc[0, 'usuario'] == 'Pedro'
        assert resultado.loc[1, 'usuario'] == 'Ana'

    def test_tarefa_id_inexistente(self):
        df_tempo = pd.DataFrame({
            'tarefa_id': [1, 999],
            'usuario': ['João', 'Maria']
        })
        df_tarefas = pd.DataFrame({
            'id': [1],
            'responsavel': ['Pedro']
        })
        
        resultado = corrigir_inconsistencia_1(df_tempo, df_tarefas)
        
        assert resultado.loc[0, 'usuario'] == 'Pedro'
        assert resultado.loc[1, 'usuario'] == 'Maria'

    def test_dataframe_vazio(self):
        df_tempo = pd.DataFrame({'tarefa_id': [], 'usuario': []})
        df_tarefas = pd.DataFrame({'id': [], 'responsavel': []})
        
        resultado = corrigir_inconsistencia_1(df_tempo, df_tarefas)
        
        assert len(resultado) == 0


class TestCorrigirInconsistencia2:
    def test_corrigir_status_projeto(self):
        df_projetos = pd.DataFrame({
            'id': [1, 2],
            'programa_id': [10, 11],
            'status': ['Em andamento', 'Em andamento']
        })
        df_programas = pd.DataFrame({
            'id': [10, 11],
            'status': ['Concluído', 'Em andamento']
        })
        
        resultado = corrigir_inconsistencia_2(df_projetos, df_programas)
        
        assert resultado.loc[0, 'status'] == STATUS_CONCLUIDO
        assert resultado.loc[1, 'status'] == 'Em andamento'

    def test_projetos_ja_concluidos(self):
        df_projetos = pd.DataFrame({
            'id': [1, 2],
            'programa_id': [10, 11],
            'status': ['Concluído', 'Em andamento']
        })
        df_programas = pd.DataFrame({
            'id': [10, 11],
            'status': ['Concluído', 'Em andamento']
        })
        
        resultado = corrigir_inconsistencia_2(df_projetos, df_programas)
        
        assert resultado.loc[0, 'status'] == STATUS_CONCLUIDO
        assert resultado.loc[1, 'status'] == 'Em andamento'


class TestCorrigirInconsistencia3:
    def test_corrigir_status_tarefa(self):
        df_tarefas = pd.DataFrame({
            'id': [1, 2],
            'projeto_id': [100, 101],
            'status': ['Em andamento', 'Em andamento']
        })
        df_projetos = pd.DataFrame({
            'id': [100, 101],
            'status': ['Concluído', 'Em andamento']
        })
        
        resultado = corrigir_inconsistencia_3(df_tarefas, df_projetos)
        
        assert resultado.loc[0, 'status'] == STATUS_CONCLUIDA
        assert resultado.loc[1, 'status'] == 'Em andamento'

    def test_tarefas_ja_concluidas(self):
        df_tarefas = pd.DataFrame({
            'id': [1, 2],
            'projeto_id': [100, 101],
            'status': ['Concluída', 'Em andamento']
        })
        df_projetos = pd.DataFrame({
            'id': [100, 101],
            'status': ['Concluído', 'Em andamento']
        })
        
        resultado = corrigir_inconsistencia_3(df_tarefas, df_projetos)
        
        assert resultado.loc[0, 'status'] == STATUS_CONCLUIDA
        assert resultado.loc[1, 'status'] == 'Em andamento'


class TestParsearDataFim:
    def test_parsear_string_data_valida(self):
        resultado = _parsear_data_fim('2026-04-14')
        assert isinstance(resultado, date)
        assert resultado == date(2026, 4, 14)

    def test_parsear_data_ja_date(self):
        data_teste = date(2026, 4, 14)
        resultado = _parsear_data_fim(data_teste)
        assert resultado == data_teste

    def test_parsear_data_invalida(self):
        resultado = _parsear_data_fim('data-invalida')
        assert resultado is None

    def test_parsear_nan(self):
        resultado = _parsear_data_fim(np.nan)
        assert resultado is None

    def test_parsear_none(self):
        resultado = _parsear_data_fim(None)
        assert resultado is None

    def test_parsear_datetime_object(self):
        dt = datetime(2026, 4, 14, 10, 30, 0)
        resultado = _parsear_data_fim(dt)
        assert resultado == dt


class TestDeterminarNovoStatus:
    def test_data_passada(self):
        data_passada = date(2026, 1, 1)
        data_atual = date(2026, 4, 14)
        resultado = _determinar_novo_status(data_passada, data_atual)
        assert resultado == STATUS_CONCLUIDA

    def test_data_futura(self):
        data_futura = date(2026, 12, 31)
        data_atual = date(2026, 4, 14)
        resultado = _determinar_novo_status(data_futura, data_atual)
        assert resultado == 'Em andamento'

    def test_data_hoje(self):
        data_hoje = date(2026, 4, 14)
        data_atual = date(2026, 4, 14)
        resultado = _determinar_novo_status(data_hoje, data_atual)
        assert resultado == 'Em andamento'

    def test_data_none(self):
        data_atual = date(2026, 4, 14)
        resultado = _determinar_novo_status(None, data_atual)
        assert resultado == 'Em andamento'


class TestCorrigirInconsistencia4:
    def test_corrigir_tarefa_com_horas_passada(self):
        hoje = date(2026, 4, 14)
        data_passada = date(2026, 1, 1)
        
        df_tarefas = pd.DataFrame({
            'id': [1],
            'status': ['Não iniciada'],
            'data_fim_prevista': [data_passada.isoformat()]
        })
        df_tempo = pd.DataFrame({
            'tarefa_id': [1],
            'horas_trabalhadas': [5.0]
        })
        
        with patch('fix_csv.datetime') as mock_dt:
            mock_dt.now.return_value.date.return_value = hoje
            mock_dt.strptime = datetime.strptime
            resultado = corrigir_inconsistencia_4(df_tarefas, df_tempo)
        
        assert resultado.loc[0, 'status'] == STATUS_CONCLUIDA

    def test_corrigir_tarefa_com_horas_futura(self):
        hoje = date(2026, 4, 14)
        data_futura = date(2026, 12, 31)
        
        df_tarefas = pd.DataFrame({
            'id': [1],
            'status': ['Não iniciada'],
            'data_fim_prevista': [data_futura.isoformat()]
        })
        df_tempo = pd.DataFrame({
            'tarefa_id': [1],
            'horas_trabalhadas': [5.0]
        })
        
        with patch('fix_csv.datetime') as mock_dt:
            mock_dt.now.return_value.date.return_value = hoje
            mock_dt.strptime = datetime.strptime
            resultado = corrigir_inconsistencia_4(df_tarefas, df_tempo)
        
        assert resultado.loc[0, 'status'] == 'Em andamento'

    def test_tarefa_sem_horas(self):
        df_tarefas = pd.DataFrame({
            'id': [1],
            'status': ['Não iniciada'],
            'data_fim_prevista': ['2026-01-01']
        })
        df_tempo = pd.DataFrame({
            'tarefa_id': [1],
            'horas_trabalhadas': [0.0]
        })
        
        resultado = corrigir_inconsistencia_4(df_tarefas, df_tempo)
        
        assert resultado.loc[0, 'status'] == 'Não iniciada'

    def test_tarefa_ja_iniciada(self):
        df_tarefas = pd.DataFrame({
            'id': [1],
            'status': ['Em andamento'],
            'data_fim_prevista': ['2026-01-01']
        })
        df_tempo = pd.DataFrame({
            'tarefa_id': [1],
            'horas_trabalhadas': [5.0]
        })
        
        resultado = corrigir_inconsistencia_4(df_tarefas, df_tempo)
        
        assert resultado.loc[0, 'status'] == 'Em andamento'

    def test_data_fim_invalida(self):
        df_tarefas = pd.DataFrame({
            'id': [1],
            'status': ['Não iniciada'],
            'data_fim_prevista': ['data-invalida']
        })
        df_tempo = pd.DataFrame({
            'tarefa_id': [1],
            'horas_trabalhadas': [5.0]
        })
        
        resultado = corrigir_inconsistencia_4(df_tarefas, df_tempo)
        
        assert resultado.loc[0, 'status'] == 'Em andamento'

    def test_data_fim_null(self):
        df_tarefas = pd.DataFrame({
            'id': [1],
            'status': ['Não iniciada'],
            'data_fim_prevista': [None]
        })
        df_tempo = pd.DataFrame({
            'tarefa_id': [1],
            'horas_trabalhadas': [5.0]
        })
        
        resultado = corrigir_inconsistencia_4(df_tarefas, df_tempo)
        
        assert resultado.loc[0, 'status'] == 'Em andamento'


class TestCorrigirProgramasConcluidos:
    def test_cascata_completa(self):
        df_programas = pd.DataFrame({
            'id': [1],
            'status': [STATUS_CONCLUIDO]
        })
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [1],
            'status': ['Em andamento']
        })
        df_tarefas = pd.DataFrame({
            'id': [100],
            'projeto_id': [10],
            'status': ['Em andamento']
        })
        
        proj_resultado, tar_resultado = corrigir_programas_concluidos(
            df_programas, df_projetos, df_tarefas
        )
        
        assert proj_resultado.loc[0, 'status'] == STATUS_CONCLUIDO
        assert tar_resultado.loc[0, 'status'] == STATUS_CONCLUIDA

    def test_sem_programas_concluidos(self):
        df_programas = pd.DataFrame({
            'id': [1],
            'status': ['Em andamento']
        })
        df_projetos = pd.DataFrame({
            'id': [10],
            'programa_id': [1],
            'status': ['Em andamento']
        })
        df_tarefas = pd.DataFrame({
            'id': [100],
            'projeto_id': [10],
            'status': ['Em andamento']
        })
        
        proj_resultado, tar_resultado = corrigir_programas_concluidos(
            df_programas, df_projetos, df_tarefas
        )
        
        assert proj_resultado.loc[0, 'status'] == 'Em andamento'
        assert tar_resultado.loc[0, 'status'] == 'Em andamento'

    def test_multiplos_programas_e_projetos(self):
        df_programas = pd.DataFrame({
            'id': [1, 2],
            'status': [STATUS_CONCLUIDO, 'Em andamento']
        })
        df_projetos = pd.DataFrame({
            'id': [10, 11],
            'programa_id': [1, 2],
            'status': ['Em andamento', 'Não iniciado']
        })
        df_tarefas = pd.DataFrame({
            'id': [100, 101],
            'projeto_id': [10, 11],
            'status': ['Não iniciada', 'Não iniciada']
        })
        
        proj_resultado, tar_resultado = corrigir_programas_concluidos(
            df_programas, df_projetos, df_tarefas
        )
        
        assert proj_resultado.loc[0, 'status'] == STATUS_CONCLUIDO
        assert proj_resultado.loc[1, 'status'] == 'Não iniciado'
        assert tar_resultado.loc[0, 'status'] == STATUS_CONCLUIDA
        assert tar_resultado.loc[1, 'status'] == 'Não iniciada'


class TestMain:
    @patch('builtins.print')
    @patch('fix_csv.salvar_csv')
    @patch('fix_csv.corrigir_programas_concluidos')
    @patch('fix_csv.corrigir_inconsistencia_4')
    @patch('fix_csv.corrigir_inconsistencia_3')
    @patch('fix_csv.corrigir_inconsistencia_2')
    @patch('fix_csv.corrigir_inconsistencia_1')
    @patch('fix_csv.criar_pasta_saida')
    @patch('fix_csv.pd.read_csv')
    def test_main_sucesso(
        self,
        mock_read_csv,
        mock_criar_pasta,
        mock_corr1,
        mock_corr2,
        mock_corr3,
        mock_corr4,
        mock_corr_cascata,
        mock_salvar,
        mock_print,
    ):
        df_tempo = pd.DataFrame({'tarefa_id': [1], 'usuario': ['João']})
        df_tarefas = pd.DataFrame({'id': [1], 'responsavel': ['Pedro']})
        df_projetos = pd.DataFrame({'id': [1], 'programa_id': [1], 'status': ['Em andamento']})
        df_programas = pd.DataFrame({'id': [1], 'status': ['Em andamento']})
        
        mock_read_csv.side_effect = [df_tempo, df_tarefas, df_projetos, df_programas]
        mock_corr1.return_value = df_tempo
        mock_corr2.return_value = df_projetos
        mock_corr3.return_value = df_tarefas
        mock_corr4.return_value = df_tarefas
        mock_corr_cascata.return_value = (df_projetos, df_tarefas)
        
        resultado = main()
        
        assert resultado == 0
        assert mock_criar_pasta.called
        assert mock_salvar.call_count == 3

    @patch('builtins.print')
    @patch('fix_csv.pd.read_csv')
    def test_main_arquivo_nao_encontrado(self, mock_read_csv, mock_print):
        mock_read_csv.side_effect = FileNotFoundError("Arquivo não encontrado")
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1

    @patch('builtins.print')
    @patch('fix_csv.salvar_csv')
    @patch('fix_csv.corrigir_programas_concluidos')
    @patch('fix_csv.corrigir_inconsistencia_4')
    @patch('fix_csv.corrigir_inconsistencia_3')
    @patch('fix_csv.corrigir_inconsistencia_2')
    @patch('fix_csv.corrigir_inconsistencia_1')
    @patch('fix_csv.criar_pasta_saida')
    @patch('fix_csv.pd.read_csv')
    def test_main_com_dados_reais_simulados(
        self,
        mock_read_csv,
        mock_criar_pasta,
        mock_corr1,
        mock_corr2,
        mock_corr3,
        mock_corr4,
        mock_corr_cascata,
        mock_salvar,
        mock_print,
    ):
        df_tempo = pd.DataFrame({
            'tarefa_id': [1, 1, 2],
            'usuario': ['João', 'João', 'Maria'],
            'horas_trabalhadas': [8.0, 4.0, 10.0]
        })
        df_tarefas = pd.DataFrame({
            'id': [1, 2],
            'responsavel': ['Pedro', 'Ana'],
            'status': ['Em andamento', 'Não iniciada'],
            'data_fim_prevista': ['2026-05-01', '2026-06-01']
        })
        df_projetos = pd.DataFrame({
            'id': [10, 11],
            'programa_id': [100, 101],
            'status': ['Em andamento', 'Em andamento']
        })
        df_programas = pd.DataFrame({
            'id': [100, 101],
            'status': ['Em andamento', 'Concluído']
        })
        
        mock_read_csv.side_effect = [df_tempo, df_tarefas, df_projetos, df_programas]
        mock_corr1.return_value = df_tempo
        mock_corr2.return_value = df_projetos
        mock_corr3.return_value = df_tarefas
        mock_corr4.return_value = df_tarefas
        mock_corr_cascata.return_value = (df_projetos, df_tarefas)
        
        resultado = main()
        
        assert resultado == 0

        mock_corr1.assert_called_once()
        mock_corr2.assert_called_once()
        mock_corr3.assert_called_once()
        mock_corr4.assert_called_once()
        mock_corr_cascata.assert_called_once()


class TestIntegracaoCompleta:
    def test_fluxo_completo_correcoes(self):
        df_tempo = pd.DataFrame({
            'tarefa_id': [1, 2],
            'usuario': ['João', 'Maria']
        })
        df_tarefas = pd.DataFrame({
            'id': [1, 2],
            'projeto_id': [10, 11],
            'responsavel': ['Pedro', 'Ana'],
            'status': ['Em andamento', 'Não iniciada'],
            'data_fim_prevista': ['2026-01-01', '2026-12-31']
        })
        df_projetos = pd.DataFrame({
            'id': [10, 11],
            'programa_id': [100, 101],
            'status': ['Em andamento', 'Em andamento']
        })
        df_programas = pd.DataFrame({
            'id': [100, 101],
            'status': ['Concluído', 'Em andamento']
        })
        
        df_tempo_corrigido = corrigir_inconsistencia_1(df_tempo, df_tarefas)
        df_projetos_corrigido = corrigir_inconsistencia_2(df_projetos, df_programas)
        df_tarefas_corrigido = corrigir_inconsistencia_3(df_tarefas, df_projetos_corrigido)
        
        assert df_tempo_corrigido.loc[0, 'usuario'] == 'Pedro'
        assert df_projetos_corrigido.loc[0, 'status'] == STATUS_CONCLUIDO
        assert df_tarefas_corrigido.loc[0, 'status'] == STATUS_CONCLUIDA

    def test_constantes_status(self):
        assert STATUS_CONCLUIDO == 'Concluído'
        assert STATUS_CONCLUIDA == 'Concluída'


@pytest.fixture
def dados_teste():
    return {
        'df_tempo': pd.DataFrame({
            'tarefa_id': [1, 2],
            'usuario': ['João', 'Maria'],
            'horas_trabalhadas': [5.0, 10.0]
        }),
        'df_tarefas': pd.DataFrame({
            'id': [1, 2],
            'projeto_id': [10, 11],
            'responsavel': ['Pedro', 'Ana'],
            'status': ['Em andamento', 'Não iniciada'],
            'data_fim_prevista': ['2026-05-01', '2026-06-01']
        }),
        'df_projetos': pd.DataFrame({
            'id': [10, 11],
            'programa_id': [100, 101],
            'status': ['Em andamento', 'Não iniciado']
        }),
        'df_programas': pd.DataFrame({
            'id': [100, 101],
            'status': ['Em andamento', 'Concluído']
        })
    }


class TestComFixture:
    def test_corr1_com_fixture(self, dados_teste):
        resultado = corrigir_inconsistencia_1(
            dados_teste['df_tempo'],
            dados_teste['df_tarefas']
        )
        assert resultado.loc[0, 'usuario'] == 'Pedro'

    def test_corr2_com_fixture(self, dados_teste):
        resultado = corrigir_inconsistencia_2(
            dados_teste['df_projetos'],
            dados_teste['df_programas']
        )
        assert resultado.loc[1, 'status'] == STATUS_CONCLUIDO

    def test_corr3_com_fixture(self, dados_teste):

        df_proj_corrigido = corrigir_inconsistencia_2(
            dados_teste['df_projetos'],
            dados_teste['df_programas']
        )

        resultado = corrigir_inconsistencia_3(
            dados_teste['df_tarefas'],
            df_proj_corrigido
        )
        assert resultado.loc[1, 'status'] == STATUS_CONCLUIDA
