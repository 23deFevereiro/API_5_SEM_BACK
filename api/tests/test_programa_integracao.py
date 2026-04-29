import pytest
from datetime import date
from pytest import approx
from model_bakery import baker
from api.services.programa_svc import (
    listar_programas,
    get_resumo_programa,
    get_distribuicao_status,
    get_burnup_horas_programas,
)
from model_bakery.recipe import seq


@pytest.mark.django_db
class TestListarProgramas:

    def test_retorna_lista_vazia_quando_nao_ha_programas(self):
        resultado = listar_programas()
        assert resultado == []

    def test_retorna_programas_quando_existem(self):
        baker.make('api.DimPrograma', _quantity=3)
        resultado = listar_programas()
        assert len(resultado) == 3

    def test_filtra_por_nome_quando_search_informado(self):
        baker.make('api.DimPrograma', nome_programa='Programa Alpha')
        baker.make('api.DimPrograma', nome_programa='Programa Beta')
        resultado = listar_programas(search='Alpha')
        assert len(resultado) == 1
        assert resultado[0]['nome_programa'] == 'Programa Alpha'

    def test_retorna_campos_id_e_nome(self):
        baker.make('api.DimPrograma', nome_programa='Aeroespacial')
        resultado = listar_programas()
        assert 'id' in resultado[0]
        assert 'codigo_programa' in resultado[0]
        assert 'nome_programa' in resultado[0]


@pytest.mark.django_db
class TestGetResumoProjeto:

    def _make_tempo(self):
        return baker.make('api.DimTempo', id=20230101, data='2023-01-01', ano=2023, mes=1, trimestre=1, semestre=1, dia_semana=0)

    def test_retorna_zeros_quando_programa_sem_dados(self):
        programa = baker.make('api.DimPrograma')
        resultado = get_resumo_programa(programa.id)
        assert resultado['total_projetos'] == 0
        assert resultado['horas_estimadas'] == approx(0.0)
        assert resultado['horas_realizadas'] == approx(0.0)
        assert resultado['custo_estimado'] == approx(0.0)
        assert resultado['custo_real'] == approx(0.0)

    def test_conta_total_projetos_corretamente(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa)
        baker.make('api.DimProjeto', id=2, programa=programa)
        baker.make('api.DimProjeto', id=3, programa=programa)
        resultado = get_resumo_programa(programa.id)
        assert resultado['total_projetos'] == 3

    def test_retorna_campos_corretos(self):
        baker.make('api.DimPrograma', nome_programa='Defesa')
        resultado = listar_programas()
        assert len(resultado) == 1
        assert resultado[0]['nome_programa'] == 'Defesa'

    def test_calcula_horas_realizadas_corretamente(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo()
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=8.0, custo_horas=0)
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=4.0, custo_horas=0)
        resultado = get_resumo_programa(programa.id)
        assert resultado['horas_realizadas'] == approx(12.0)

    def test_calcula_custo_estimado_mao_de_obra(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo()
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=10.0, custo_horas=500.0)
        resultado = get_resumo_programa(programa.id)
        assert resultado['custo_estimado'] == approx(500.0)

    def test_calcula_custo_estimado_materiais(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo()
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa, tempo=tempo, custo_materiais=500.0)
        resultado = get_resumo_programa(programa.id)
        assert resultado['custo_estimado'] == approx(500.0)

    def test_calcula_custo_real_mao_de_obra(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo()
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=10.0, custo_horas=500.0)
        resultado = get_resumo_programa(programa.id)
        assert resultado['custo_real'] == approx(500.0)

    def test_exclui_compras_canceladas_do_custo_real(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo()
        status_cancelado = baker.make('api.DimStatusPedido', nome_status='Cancelado')
        status_entregue = baker.make('api.DimStatusPedido', nome_status='Entregue')
        baker.make('api.FatoCompras', projeto=projeto, tempo=tempo, status=status_cancelado, valor_alocado=1000.00)
        baker.make('api.FatoCompras', projeto=projeto, tempo=tempo, status=status_entregue, valor_alocado=500.00)
        resultado = get_resumo_programa(programa.id)
        assert resultado['custo_real'] == approx(500.0)

    def test_nao_inclui_dados_de_outro_programa(self):
        programa1 = baker.make('api.DimPrograma')
        programa2 = baker.make('api.DimPrograma')
        for i in range(10, 15):
            baker.make('api.DimProjeto', id=i, programa=programa2)
        resultado = get_resumo_programa(programa1.id)
        assert resultado['total_projetos'] == 0


@pytest.mark.django_db
class TestGetDistribuicaoStatus:

    def test_retorna_total_zero_quando_programa_sem_projetos(self):
        programa = baker.make('api.DimPrograma')
        resultado = get_distribuicao_status(programa.id)
        assert resultado['total'] == 0
        assert resultado['status'] == []

    def test_retorna_apenas_status_com_projetos(self):
        programa = baker.make('api.DimPrograma')
        for i in range(1, 4):
            baker.make('api.DimProjeto', id=i, programa=programa, status='Planejamento')
        resultado = get_distribuicao_status(programa.id)
        assert len(resultado['status']) == 1
        assert resultado['status'][0]['status'] == 'Planejamento'

    def test_conta_total_corretamente(self):
        programa = baker.make('api.DimPrograma')
        for i in range(1, 5):
            baker.make('api.DimProjeto', id=i, programa=programa, status='Planejamento')
        for i in range(5, 11):
            baker.make('api.DimProjeto', id=i, programa=programa, status='Concluído')
        resultado = get_distribuicao_status(programa.id)
        assert resultado['total'] == 10

    def test_calcula_percentual_corretamente(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa, status='Planejamento')
        for i in range(2, 5):
            baker.make('api.DimProjeto', id=i, programa=programa, status='Concluído')
        resultado = get_distribuicao_status(programa.id)
        status_dict = {s['status']: s for s in resultado['status']}
        assert status_dict['Planejamento']['percentual'] == approx(25.0)
        assert status_dict['Concluído']['percentual'] == approx(75.0)

    def test_retorna_quantidade_absoluta_corretamente(self):
        programa = baker.make('api.DimPrograma')
        for i in range(1, 6):
            baker.make('api.DimProjeto', id=i, programa=programa, status='Em andamento')
        resultado = get_distribuicao_status(programa.id)
        assert resultado['status'][0]['quantidade'] == 5

    def test_retorna_cor_correta_por_status(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa, status='Planejamento')
        baker.make('api.DimProjeto', id=2, programa=programa, status='Em andamento')
        baker.make('api.DimProjeto', id=3, programa=programa, status='Suspenso')
        baker.make('api.DimProjeto', id=4, programa=programa, status='Concluído')
        resultado = get_distribuicao_status(programa.id)
        status_dict = {s['status']: s for s in resultado['status']}
        assert status_dict['Planejamento']['cor'] == '#3B82F6'
        assert status_dict['Em andamento']['cor'] == '#EAB308'
        assert status_dict['Suspenso']['cor'] == '#F97316'
        assert status_dict['Concluído']['cor'] == '#22C55E'

    def test_nao_inclui_projetos_de_outro_programa(self):
        programa1 = baker.make('api.DimPrograma')
        programa2 = baker.make('api.DimPrograma')
        for i in range(1, 6):
            baker.make('api.DimProjeto', id=i, programa=programa2, status='Planejamento')
        resultado = get_distribuicao_status(programa1.id)
        assert resultado['total'] == 0
        assert resultado['status'] == []

    def test_retorna_todos_os_quatro_status_quando_presentes(self):
        programa = baker.make('api.DimPrograma')
        for i in range(1, 3):
            baker.make('api.DimProjeto', id=i, programa=programa, status='Planejamento')
        for i in range(3, 6):
            baker.make('api.DimProjeto', id=i, programa=programa, status='Em andamento')
        baker.make('api.DimProjeto', id=6, programa=programa, status='Suspenso')
        for i in range(7, 11):
            baker.make('api.DimProjeto', id=i, programa=programa, status='Concluído')
        resultado = get_distribuicao_status(programa.id)
        assert len(resultado['status']) == 4
        assert resultado['total'] == 10


@pytest.mark.django_db
class TestGetBurnupHorasProgramas:

    def _make_tempo(self, ano, mes, dia=1):
        from api.models import DimTempo
        _id = ano * 10000 + mes * 100 + dia
        existente = DimTempo.objects.filter(id=_id).first()
        if existente:
            return existente
        return baker.make(
            'api.DimTempo',
            id=_id,
            data=date(ano, mes, dia),
            ano=ano,
            mes=mes,
            trimestre=(mes - 1) // 3 + 1,
            semestre=1 if mes <= 6 else 2,
            dia_semana=date(ano, mes, dia).weekday(),
        )

    def test_retorna_lista_vazia_sem_registros_de_horas(self):
        resultado = get_burnup_horas_programas()
        assert resultado == []

    def test_retorna_lista_vazia_quando_so_existem_programas_sem_horas(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa)
        resultado = get_burnup_horas_programas()
        assert resultado == []

    def test_agrupa_horas_por_mes_e_ano(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo1 = self._make_tempo(2025, 1, 5)
        tempo2 = self._make_tempo(2025, 1, 20)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo1, horas_trabalhadas=4.0, custo_horas=0)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo2, horas_trabalhadas=6.0, custo_horas=0)
        resultado = get_burnup_horas_programas()
        assert len(resultado) == 1
        assert resultado[0]['date_str'] == '01/2025'
        assert resultado[0]['values'][0]['horas'] == approx(10.0)

    def test_acumula_horas_ao_longo_dos_meses(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo_jan = self._make_tempo(2025, 1, 10)
        tempo_fev = self._make_tempo(2025, 2, 10)
        tempo_mar = self._make_tempo(2025, 3, 10)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_jan, horas_trabalhadas=10.0, custo_horas=0)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_fev, horas_trabalhadas=5.0, custo_horas=0)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_mar, horas_trabalhadas=3.0, custo_horas=0)
        resultado = get_burnup_horas_programas()
        horas_por_mes = {g['date_str']: g['values'][0]['horas'] for g in resultado}
        assert horas_por_mes['01/2025'] == approx(10.0)
        assert horas_por_mes['02/2025'] == approx(15.0)
        assert horas_por_mes['03/2025'] == approx(18.0)

    def test_separa_series_por_programa(self):
        programa1 = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        programa2 = baker.make('api.DimPrograma', codigo_programa='PROG-2', nome_programa='Beta')
        projeto1 = baker.make('api.DimProjeto', id=1, programa=programa1)
        projeto2 = baker.make('api.DimProjeto', id=2, programa=programa2)
        tempo = self._make_tempo(2025, 1, 10)
        baker.make('api.FatoHoras', programa=programa1, projeto=projeto1,
                   tempo=tempo, horas_trabalhadas=8.0, custo_horas=0)
        baker.make('api.FatoHoras', programa=programa2, projeto=projeto2,
                   tempo=tempo, horas_trabalhadas=12.0, custo_horas=0)
        resultado = get_burnup_horas_programas()
        assert len(resultado) == 1
        valores = {v['codigo_programa']: v['horas'] for v in resultado[0]['values']}
        assert valores['PROG-1'] == approx(8.0)
        assert valores['PROG-2'] == approx(12.0)

    def test_inclui_programas_independente_do_status_do_projeto(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa, status='Concluído')
        tempo = self._make_tempo(2025, 1, 10)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo, horas_trabalhadas=4.0, custo_horas=0)
        resultado = get_burnup_horas_programas()
        assert len(resultado) == 1
        assert resultado[0]['values'][0]['codigo_programa'] == 'PROG-1'

    def test_ordena_grupos_por_ano_e_mes_ascendente(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo_mar = self._make_tempo(2025, 3, 10)
        tempo_dez = self._make_tempo(2024, 12, 10)
        tempo_jan = self._make_tempo(2025, 1, 10)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_mar, horas_trabalhadas=3.0, custo_horas=0)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_dez, horas_trabalhadas=2.0, custo_horas=0)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_jan, horas_trabalhadas=1.0, custo_horas=0)
        resultado = get_burnup_horas_programas()
        datas = [g['date_str'] for g in resultado]
        assert datas == ['12/2024', '01/2025', '03/2025']

    def test_retorna_estrutura_correta_dos_valores(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo(2025, 1, 10)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo, horas_trabalhadas=2.0, custo_horas=0)
        resultado = get_burnup_horas_programas()
        ponto = resultado[0]['values'][0]
        assert 'codigo_programa' in ponto
        assert 'nome_programa' in ponto
        assert 'horas' in ponto
        assert isinstance(ponto['horas'], float)

    def test_acumula_independente_para_cada_programa(self):
        programa1 = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        programa2 = baker.make('api.DimPrograma', codigo_programa='PROG-2', nome_programa='Beta')
        projeto1 = baker.make('api.DimProjeto', id=1, programa=programa1)
        projeto2 = baker.make('api.DimProjeto', id=2, programa=programa2)
        tempo_jan = self._make_tempo(2025, 1, 10)
        tempo_fev = self._make_tempo(2025, 2, 10)
        tempo_mar = self._make_tempo(2025, 3, 10)
        baker.make('api.FatoHoras', programa=programa1, projeto=projeto1,
                   tempo=tempo_jan, horas_trabalhadas=10.0, custo_horas=0)
        baker.make('api.FatoHoras', programa=programa2, projeto=projeto2,
                   tempo=tempo_fev, horas_trabalhadas=20.0, custo_horas=0)
        baker.make('api.FatoHoras', programa=programa1, projeto=projeto1,
                   tempo=tempo_mar, horas_trabalhadas=5.0, custo_horas=0)
        resultado = get_burnup_horas_programas()
        grupos = {g['date_str']: g for g in resultado}
        valores_marco = {v['codigo_programa']: v['horas'] for v in grupos['03/2025']['values']}
        assert valores_marco['PROG-1'] == approx(15.0)
        assert 'PROG-2' not in valores_marco

    def test_soma_horas_de_multiplos_projetos_do_mesmo_programa(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto1 = baker.make('api.DimProjeto', id=1, programa=programa)
        projeto2 = baker.make('api.DimProjeto', id=2, programa=programa)
        tempo1 = self._make_tempo(2025, 1, 10)
        tempo2 = self._make_tempo(2025, 1, 15)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto1,
                   tempo=tempo1, horas_trabalhadas=4.0, custo_horas=0)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto2,
                   tempo=tempo2, horas_trabalhadas=6.0, custo_horas=0)
        resultado = get_burnup_horas_programas()
        assert resultado[0]['values'][0]['horas'] == approx(10.0)