import pytest
from datetime import date
from pytest import approx
from decimal import Decimal
from django.http import Http404
from model_bakery import baker
from api.services.programa_svc import (
    listar_programas,
    get_resumo_programa,
    get_distribuicao_status,
    get_burnup_horas_programas,
    get_burnup_custo_programas,
    get_tabela_projetos,
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


@pytest.mark.django_db
class TestGetBurnupCustoProgramas:

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

    def test_retorna_lista_vazia_sem_registros(self):
        resultado = get_burnup_custo_programas()
        assert resultado == []

    def test_retorna_lista_vazia_quando_so_existem_programas_sem_lancamentos(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa)
        resultado = get_burnup_custo_programas()
        assert resultado == []

    def test_soma_apenas_custo_de_mao_de_obra(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo(2025, 1, 10)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo, horas_trabalhadas=10.0, custo_horas=500.0)
        resultado = get_burnup_custo_programas()
        assert len(resultado) == 1
        assert resultado[0]['values'][0]['custo'] == approx(500.0)

    def test_soma_apenas_custo_de_compras(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo(2025, 1, 10)
        status = baker.make('api.DimStatusPedido', nome_status='Entregue')
        baker.make('api.FatoCompras', projeto=projeto, tempo=tempo,
                   status=status, valor_alocado=300.0)
        resultado = get_burnup_custo_programas()
        assert len(resultado) == 1
        assert resultado[0]['values'][0]['custo'] == approx(300.0)

    def test_soma_combinada_mao_de_obra_e_compras(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo(2025, 1, 10)
        status = baker.make('api.DimStatusPedido', nome_status='Entregue')
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo, horas_trabalhadas=8.0, custo_horas=400.0)
        baker.make('api.FatoCompras', projeto=projeto, tempo=tempo,
                   status=status, valor_alocado=600.0)
        resultado = get_burnup_custo_programas()
        assert resultado[0]['values'][0]['custo'] == approx(1000.0)

    def test_exclui_compras_canceladas(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo(2025, 1, 10)
        cancelado = baker.make('api.DimStatusPedido', nome_status='Cancelado')
        entregue = baker.make('api.DimStatusPedido', nome_status='Entregue')
        baker.make('api.FatoCompras', projeto=projeto, tempo=tempo,
                   status=cancelado, valor_alocado=1000.0)
        baker.make('api.FatoCompras', projeto=projeto, tempo=tempo,
                   status=entregue, valor_alocado=200.0)
        resultado = get_burnup_custo_programas()
        assert resultado[0]['values'][0]['custo'] == approx(200.0)

    def test_acumula_custo_ao_longo_dos_meses(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo_jan = self._make_tempo(2025, 1, 10)
        tempo_fev = self._make_tempo(2025, 2, 10)
        tempo_mar = self._make_tempo(2025, 3, 10)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_jan, horas_trabalhadas=0, custo_horas=100.0)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_fev, horas_trabalhadas=0, custo_horas=50.0)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_mar, horas_trabalhadas=0, custo_horas=30.0)
        resultado = get_burnup_custo_programas()
        custo_por_mes = {g['date_str']: g['values'][0]['custo'] for g in resultado}
        assert custo_por_mes['01/2025'] == approx(100.0)
        assert custo_por_mes['02/2025'] == approx(150.0)
        assert custo_por_mes['03/2025'] == approx(180.0)

    def test_separa_series_por_programa(self):
        programa1 = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        programa2 = baker.make('api.DimPrograma', codigo_programa='PROG-2', nome_programa='Beta')
        projeto1 = baker.make('api.DimProjeto', id=1, programa=programa1)
        projeto2 = baker.make('api.DimProjeto', id=2, programa=programa2)
        tempo = self._make_tempo(2025, 1, 10)
        baker.make('api.FatoHoras', programa=programa1, projeto=projeto1,
                   tempo=tempo, horas_trabalhadas=0, custo_horas=400.0)
        baker.make('api.FatoHoras', programa=programa2, projeto=projeto2,
                   tempo=tempo, horas_trabalhadas=0, custo_horas=600.0)
        resultado = get_burnup_custo_programas()
        assert len(resultado) == 1
        valores = {v['codigo_programa']: v['custo'] for v in resultado[0]['values']}
        assert valores['PROG-1'] == approx(400.0)
        assert valores['PROG-2'] == approx(600.0)

    def test_ordena_grupos_cronologicamente(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo_mar = self._make_tempo(2025, 3, 10)
        tempo_dez = self._make_tempo(2024, 12, 10)
        tempo_jan = self._make_tempo(2025, 1, 10)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_mar, horas_trabalhadas=0, custo_horas=30.0)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_dez, horas_trabalhadas=0, custo_horas=20.0)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo_jan, horas_trabalhadas=0, custo_horas=10.0)
        resultado = get_burnup_custo_programas()
        datas = [g['date_str'] for g in resultado]
        assert datas == ['12/2024', '01/2025', '03/2025']

    def test_retorna_estrutura_correta_dos_valores(self):
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo(2025, 1, 10)
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo, horas_trabalhadas=0, custo_horas=50.0)
        resultado = get_burnup_custo_programas()
        ponto = resultado[0]['values'][0]
        assert 'codigo_programa' in ponto
        assert 'nome_programa' in ponto
        assert 'custo' in ponto
        assert isinstance(ponto['custo'], Decimal)

    def test_acumula_independente_para_cada_programa(self):
        programa1 = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        programa2 = baker.make('api.DimPrograma', codigo_programa='PROG-2', nome_programa='Beta')
        projeto1 = baker.make('api.DimProjeto', id=1, programa=programa1)
        projeto2 = baker.make('api.DimProjeto', id=2, programa=programa2)
        tempo_jan = self._make_tempo(2025, 1, 10)
        tempo_fev = self._make_tempo(2025, 2, 10)
        tempo_mar = self._make_tempo(2025, 3, 10)
        baker.make('api.FatoHoras', programa=programa1, projeto=projeto1,
                   tempo=tempo_jan, horas_trabalhadas=0, custo_horas=100.0)
        baker.make('api.FatoHoras', programa=programa2, projeto=projeto2,
                   tempo=tempo_fev, horas_trabalhadas=0, custo_horas=200.0)
        baker.make('api.FatoHoras', programa=programa1, projeto=projeto1,
                   tempo=tempo_mar, horas_trabalhadas=0, custo_horas=50.0)
        resultado = get_burnup_custo_programas()
        grupos = {g['date_str']: g for g in resultado}
        valores_marco = {v['codigo_programa']: v['custo'] for v in grupos['03/2025']['values']}
        assert valores_marco['PROG-1'] == approx(150.0)
        assert 'PROG-2' not in valores_marco

    def test_ignora_compras_de_projeto_sem_programa(self):
        projeto_orfao = baker.make('api.DimProjeto', id=99, programa=None)
        tempo = self._make_tempo(2025, 1, 10)
        status = baker.make('api.DimStatusPedido', nome_status='Entregue')
        baker.make('api.FatoCompras', projeto=projeto_orfao, tempo=tempo,
                   status=status, valor_alocado=500.0)
        resultado = get_burnup_custo_programas()
        assert resultado == []


@pytest.mark.django_db
class TestGetTabelaProjetos:

    def _make_tempo(self):
        return baker.make(
            'api.DimTempo', id=20230101, data='2023-01-01',
            ano=2023, mes=1, trimestre=1, semestre=1, dia_semana=0,
        )

    def test_levanta_404_para_programa_inexistente(self):
        with pytest.raises(Http404):
            get_tabela_projetos(99999)

    def test_retorna_lista_vazia_quando_programa_sem_projetos(self):
        programa = baker.make('api.DimPrograma')
        resultado = get_tabela_projetos(programa.id)
        assert resultado == {
            'count': 0,
            'page': 1,
            'page_size': 10,
            'total_pages': 1,
            'results': [],
        }

    def test_retorna_um_item_por_projeto(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa)
        baker.make('api.DimProjeto', id=2, programa=programa)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['count'] == 2
        assert len(resultado['results']) == 2

    def test_retorna_campos_corretos(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa)
        resultado = get_tabela_projetos(programa.id)
        item = resultado['results'][0]
        assert 'nome_projeto' in item
        assert 'responsavel' in item
        assert 'status' in item
        assert 'horas_estimadas' in item
        assert 'horas_realizadas' in item
        assert 'percentual_tarefas_concluidas' in item
        assert 'desvio_horas' in item
        assert 'percentual_desvio' in item

    def test_retorna_zeros_quando_sem_tarefas_e_horas(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa)
        resultado = get_tabela_projetos(programa.id)
        item = resultado['results'][0]
        assert item['horas_estimadas'] == approx(0.0)
        assert item['horas_realizadas'] == approx(0.0)
        assert item['desvio_horas'] == approx(0.0)
        assert item['percentual_desvio'] == approx(0.0)
        assert item['percentual_tarefas_concluidas'] == approx(0.0)

    def test_calcula_horas_estimadas_a_partir_das_tarefas(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=10.0, status='Em andamento')
        baker.make('api.DimTarefa', id=2, projeto=projeto, horas_estimadas=5.0, status='Em andamento')
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['horas_estimadas'] == approx(15.0)

    def test_calcula_horas_realizadas_do_fato_horas(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo()
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=6.0, custo_horas=0)
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=4.0, custo_horas=0)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['horas_realizadas'] == approx(10.0)

    def test_calcula_desvio_horas_corretamente(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo()
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=10.0, status='Em andamento')
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=13.0, custo_horas=0)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['desvio_horas'] == approx(3.0)

    def test_calcula_percentual_desvio_corretamente(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo()
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=10.0, status='Em andamento')
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=12.0, custo_horas=0)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['percentual_desvio'] == approx(20.0)

    def test_calcula_percentual_tarefas_concluidas(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        baker.make('api.DimTarefa', id=2, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        baker.make('api.DimTarefa', id=3, projeto=projeto, horas_estimadas=5.0, status='Em andamento')
        baker.make('api.DimTarefa', id=4, projeto=projeto, horas_estimadas=5.0, status='Em andamento')
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['percentual_tarefas_concluidas'] == approx(50.0)

    def test_percentual_tarefas_cem_por_cento_quando_todas_concluidas(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        baker.make('api.DimTarefa', id=2, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['percentual_tarefas_concluidas'] == approx(100.0)

    def test_nao_inclui_projetos_de_outro_programa(self):
        programa1 = baker.make('api.DimPrograma')
        programa2 = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa2)
        baker.make('api.DimProjeto', id=2, programa=programa2)
        resultado = get_tabela_projetos(programa1.id)
        assert resultado['results'] == []

    def test_retorna_nome_responsavel_e_status_do_projeto(self):
        programa = baker.make('api.DimPrograma')
        baker.make(
            'api.DimProjeto', id=1, programa=programa,
            nome_projeto='Projeto X', responsavel='João', status='Em andamento',
        )
        resultado = get_tabela_projetos(programa.id)
        item = resultado['results'][0]
        assert item['nome_projeto'] == 'Projeto X'
        assert item['responsavel'] == 'João'
        assert item['status'] == 'Em andamento'

    def test_retorna_paginacao_da_tabela(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', programa=programa, _quantity=12)
        resultado = get_tabela_projetos(programa.id, page=2, page_size=10)
        assert resultado['count'] == 12
        assert resultado['page'] == 2
        assert resultado['page_size'] == 10
        assert resultado['total_pages'] == 2
        assert len(resultado['results']) == 2

    def test_retorna_data_ultima_atividade_quando_ha_horas(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = baker.make(
            'api.DimTempo', id=20240315, data='2024-03-15',
            ano=2024, mes=3, trimestre=1, semestre=1, dia_semana=4,
        )
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=8.0, custo_horas=0)
        resultado = get_tabela_projetos(programa.id)
        item = resultado['results'][0]
        assert item['data_ultima_atividade'] == '2024-03-15'
        assert item['dias_desde_ultima_atividade'] is not None
        assert isinstance(item['dias_desde_ultima_atividade'], int)

    def test_retorna_nulo_quando_sem_horas_registradas(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa)
        resultado = get_tabela_projetos(programa.id)
        item = resultado['results'][0]
        assert item['data_ultima_atividade'] is None
        assert item['dias_desde_ultima_atividade'] is None

    def test_sem_horas_registradas_true_quando_nao_ha_horas(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=5.0, status='Em andamento')
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['sem_horas_registradas'] is True

    def test_sem_horas_registradas_false_quando_ha_horas(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = self._make_tempo()
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=4.0, custo_horas=0)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['sem_horas_registradas'] is False

    def test_acao_suspenso_quando_projeto_suspenso(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa, status='Suspenso')
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'suspenso'

    def test_acao_check_verde_quando_concluido_sem_tarefas(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa, status='Concluído')
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'check-verde'

    def test_acao_corrigir_status_quando_todas_concluidas_e_em_andamento(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa, status='Em andamento')
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        baker.make('api.DimTarefa', id=2, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'corrigir-status'

    def test_acao_corrigir_status_quando_todas_concluidas_e_planejamento(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa, status='Planejamento')
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'corrigir-status'

    def test_acao_check_verde_quando_concluido_todas_tarefas_sem_data_fim(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa, status='Concluído', data_fim_prevista=None)
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'check-verde'

    def test_acao_check_verde_quando_concluido_todas_tarefas_dentro_do_prazo(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa, status='Concluído', data_fim_prevista=date(2024, 6, 30))
        tarefa = baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        tempo = baker.make(
            'api.DimTempo', id=20240601, data=date(2024, 6, 1),
            ano=2024, mes=6, trimestre=2, semestre=1, dia_semana=5,
        )
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tarefa=tarefa, tempo=tempo, horas_trabalhadas=5.0, custo_horas=0)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'check-verde'

    def test_acao_check_vermelho_quando_concluido_todas_tarefas_fora_do_prazo(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa, status='Concluído', data_fim_prevista=date(2024, 5, 31))
        tarefa = baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        tempo = baker.make(
            'api.DimTempo', id=20240601, data=date(2024, 6, 1),
            ano=2024, mes=6, trimestre=2, semestre=1, dia_semana=5,
        )
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tarefa=tarefa, tempo=tempo, horas_trabalhadas=5.0, custo_horas=0)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'check-vermelho'

    def test_acao_check_amarelo_quando_concluido_tarefas_mistas(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa, status='Concluído', data_fim_prevista=date(2024, 6, 15))
        tarefa1 = baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        tarefa2 = baker.make('api.DimTarefa', id=2, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        tempo_dentro = baker.make(
            'api.DimTempo', id=20240610, data=date(2024, 6, 10),
            ano=2024, mes=6, trimestre=2, semestre=1, dia_semana=0,
        )
        tempo_fora = baker.make(
            'api.DimTempo', id=20240620, data=date(2024, 6, 20),
            ano=2024, mes=6, trimestre=2, semestre=1, dia_semana=3,
        )
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tarefa=tarefa1, tempo=tempo_dentro, horas_trabalhadas=5.0, custo_horas=0)
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tarefa=tarefa2, tempo=tempo_fora, horas_trabalhadas=5.0, custo_horas=0)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'check-amarelo'

    def test_acao_priorizar_verde_quando_dentro_do_prazo(self):
        from datetime import timedelta
        programa = baker.make('api.DimPrograma')
        prazo_futuro = date.today() + timedelta(days=30)
        baker.make('api.DimProjeto', id=1, programa=programa, status='Em andamento', data_fim_prevista=prazo_futuro)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'priorizar-verde'

    def test_acao_priorizar_verde_quando_sem_data_fim(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa, status='Em andamento', data_fim_prevista=None)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'priorizar-verde'

    def test_acao_priorizar_vermelho_quando_fora_do_prazo(self):
        from datetime import timedelta
        programa = baker.make('api.DimPrograma')
        prazo_passado = date.today() - timedelta(days=10)
        baker.make('api.DimProjeto', id=1, programa=programa, status='Em andamento', data_fim_prevista=prazo_passado)
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'priorizar-vermelho'

    def test_acao_outro_quando_concluido_com_tarefas_pendentes(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa, status='Concluído')
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=5.0, status='Concluída')
        baker.make('api.DimTarefa', id=2, projeto=projeto, horas_estimadas=5.0, status='Em andamento')
        resultado = get_tabela_projetos(programa.id)
        assert resultado['results'][0]['situacao'] == 'outro'

    def test_ordena_por_nome_projeto_asc(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa, nome_projeto='Zebra')
        baker.make('api.DimProjeto', id=2, programa=programa, nome_projeto='Alpha')
        resultado = get_tabela_projetos(programa.id, sort_by='nome_projeto', sort_dir='asc')
        nomes = [r['nome_projeto'] for r in resultado['results']]
        assert nomes == sorted(nomes)

    def test_ordena_por_nome_projeto_desc(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa, nome_projeto='Alpha')
        baker.make('api.DimProjeto', id=2, programa=programa, nome_projeto='Zebra')
        resultado = get_tabela_projetos(programa.id, sort_by='nome_projeto', sort_dir='desc')
        nomes = [r['nome_projeto'] for r in resultado['results']]
        assert nomes == sorted(nomes, reverse=True)

    def test_ordena_por_status_asc(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa, status='Suspenso')
        baker.make('api.DimProjeto', id=2, programa=programa, status='Em andamento')
        baker.make('api.DimProjeto', id=3, programa=programa, status='Concluído')
        resultado = get_tabela_projetos(programa.id, sort_by='status', sort_dir='asc')
        statuses = [r['status'] for r in resultado['results']]
        assert statuses == sorted(statuses)

    def test_ordena_por_responsavel_desc(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', id=1, programa=programa, responsavel='Ana')
        baker.make('api.DimProjeto', id=2, programa=programa, responsavel='Zeca')
        resultado = get_tabela_projetos(programa.id, sort_by='responsavel', sort_dir='desc')
        responsaveis = [r['responsavel'] for r in resultado['results']]
        assert responsaveis == sorted(responsaveis, reverse=True)

    def test_ordena_por_acao_asc_respeita_ordem_de_prioridade(self):
        from datetime import timedelta
        from api.services.programa_svc import ACAO_ORDEM
        programa = baker.make('api.DimPrograma')
        prazo_passado = date.today() - timedelta(days=5)
        prazo_futuro = date.today() + timedelta(days=30)
        baker.make('api.DimProjeto', id=1, programa=programa, status='Em andamento', data_fim_prevista=prazo_futuro)
        baker.make('api.DimProjeto', id=2, programa=programa, status='Suspenso')
        baker.make('api.DimProjeto', id=3, programa=programa, status='Em andamento', data_fim_prevista=prazo_passado)
        resultado = get_tabela_projetos(programa.id, sort_by='situacao', sort_dir='asc')
        acoes = [r['situacao'] for r in resultado['results']]
        assert acoes == sorted(acoes, key=lambda a: ACAO_ORDEM.get(a, 99))

    def test_ordena_por_acao_desc_inverte_ordem(self):
        from datetime import timedelta
        from api.services.programa_svc import ACAO_ORDEM
        programa = baker.make('api.DimPrograma')
        prazo_passado = date.today() - timedelta(days=5)
        prazo_futuro = date.today() + timedelta(days=30)
        baker.make('api.DimProjeto', id=1, programa=programa, status='Suspenso')
        baker.make('api.DimProjeto', id=2, programa=programa, status='Em andamento', data_fim_prevista=prazo_passado)
        baker.make('api.DimProjeto', id=3, programa=programa, status='Em andamento', data_fim_prevista=prazo_futuro)
        resultado = get_tabela_projetos(programa.id, sort_by='situacao', sort_dir='desc')
        acoes = [r['situacao'] for r in resultado['results']]
        assert acoes == sorted(acoes, key=lambda a: ACAO_ORDEM.get(a, 99), reverse=True)

    def test_ordenacao_por_acao_pagina_corretamente(self):
        from datetime import timedelta
        programa = baker.make('api.DimPrograma')
        prazo_passado = date.today() - timedelta(days=5)
        for i in range(1, 7):
            baker.make('api.DimProjeto', id=i, programa=programa, status='Suspenso')
        for i in range(7, 13):
            baker.make('api.DimProjeto', id=i, programa=programa, status='Em andamento', data_fim_prevista=prazo_passado)
        resultado = get_tabela_projetos(programa.id, page=2, sort_by='situacao', sort_dir='asc')
        assert resultado['count'] == 12
        assert resultado['page'] == 2
        assert len(resultado['results']) == 2
