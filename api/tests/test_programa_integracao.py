import pytest
from pytest import approx
from model_bakery import baker
from api.services.programa_svc import listar_programas, get_resumo_programa, get_distribuicao_status


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