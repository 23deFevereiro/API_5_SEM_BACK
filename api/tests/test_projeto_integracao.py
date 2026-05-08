import pytest
from datetime import date
from pytest import approx
from model_bakery import baker
from django.test import RequestFactory
from api.views.projeto_view import (
    listar_projetos_view,
    get_resumo_projeto_view,
    get_materiais_projeto_view,
    get_overview_projetos,
    get_materiais_disponiveis_view,
)
from api.services.projeto_svc import (
    listar_projetos,
    get_resumo_projeto,
    get_materiais_projeto,
    get_overview_data_all,
    get_materiais_disponiveis,
)


@pytest.mark.django_db
class TestListarProjetos:

    def test_retorna_lista_vazia_quando_nao_ha_projetos(self):
        resultado = listar_projetos()
        assert resultado == []

    def test_retorna_projetos_quando_existem(self):
        baker.make('api.DimProjeto', nome_projeto='Conversor DC-DC', _quantity=3)
        resultado = listar_projetos()
        assert len(resultado) == 3

    def test_filtra_por_nome_quando_search_informado(self):
        baker.make('api.DimProjeto', nome_projeto='Conversor DC-DC')
        baker.make('api.DimProjeto', nome_projeto='Driver LED')
        resultado = listar_projetos(search='Conversor')
        assert len(resultado) == 1
        assert resultado[0]['nome_projeto'] == 'Conversor DC-DC'

    def test_retorna_campos_corretos(self):
        baker.make('api.DimProjeto', nome_projeto='Teste')
        resultado = listar_projetos()
        assert 'id' in resultado[0]
        assert 'codigo_projeto' in resultado[0]
        assert 'nome_projeto' in resultado[0]

    def test_filtra_por_programa_id(self):
        programa_a = baker.make('api.DimPrograma')
        programa_b = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', nome_projeto='Projeto A1', programa=programa_a)
        baker.make('api.DimProjeto', nome_projeto='Projeto A2', programa=programa_a)
        baker.make('api.DimProjeto', nome_projeto='Projeto B1', programa=programa_b)

        resultado = listar_projetos(programa_id=programa_a.id)

        assert len(resultado) == 2
        nomes = [p['nome_projeto'] for p in resultado]
        assert 'Projeto A1' in nomes
        assert 'Projeto A2' in nomes
        assert 'Projeto B1' not in nomes

    def test_programa_id_none_retorna_todos(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', programa=programa, _quantity=2)
        baker.make('api.DimProjeto', _quantity=1)

        resultado = listar_projetos(programa_id=None)

        assert len(resultado) == 3

    def test_retorna_vazio_para_programa_sem_projetos(self):
        baker.make('api.DimProjeto', _quantity=3)
        programa_vazio = baker.make('api.DimPrograma')

        resultado = listar_projetos(programa_id=programa_vazio.id)

        assert resultado == []

    def test_combina_search_com_programa_id(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', nome_projeto='Conversor DC-DC', programa=programa)
        baker.make('api.DimProjeto', nome_projeto='Driver LED', programa=programa)
        baker.make('api.DimProjeto', nome_projeto='Conversor AC')

        resultado = listar_projetos(search='Conversor', programa_id=programa.id)

        assert len(resultado) == 1
        assert resultado[0]['nome_projeto'] == 'Conversor DC-DC'


@pytest.mark.django_db
class TestGetResumoProjeto:

    def test_retorna_zeros_quando_projeto_sem_dados(self):
        projeto = baker.make('api.DimProjeto')
        resultado = get_resumo_projeto(projeto.id)
        assert resultado['custo_total'] == approx(0.0)
        assert resultado['tempo_total'] == approx(0.0)

    def test_calcula_custo_materiais_corretamente(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        material = baker.make('api.DimMaterial', custo_estimado=100.00)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=5, custo_materiais=500.00)
        resultado = get_resumo_projeto(projeto.id)
        assert resultado['custo_total'] == approx(500.0)

    def test_calcula_custo_total_com_mao_de_obra_e_materiais(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        funcionario = baker.make('api.DimFuncionario')
        tarefa = baker.make('api.DimTarefa', projeto=projeto)
        tempo = baker.make('api.DimTempo')
        material = baker.make('api.DimMaterial', custo_estimado=100.00)
        fornecedor = baker.make('api.DimFornecedor')
        baker.make('api.FatoHoras', projeto=projeto, programa=programa,
                   funcionario=funcionario, tarefa=tarefa, tempo=tempo,
                   horas_trabalhadas=10.0, custo_horas=500.00)
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=5, custo_materiais=500.00)
        resultado = get_resumo_projeto(projeto.id)
        assert resultado['custo_total'] == approx(1000.0)

    def test_calcula_tempo_total_das_tarefas(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        funcionario = baker.make('api.DimFuncionario')
        tarefa = baker.make('api.DimTarefa', projeto=projeto)
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoHoras', projeto=projeto, programa=programa,
                   funcionario=funcionario, tarefa=tarefa, tempo=tempo,
                   horas_trabalhadas=8.0, custo_horas=0)
        baker.make('api.FatoHoras', projeto=projeto, programa=programa,
                   funcionario=funcionario, tarefa=tarefa, tempo=tempo,
                   horas_trabalhadas=4.5, custo_horas=0)
        resultado = get_resumo_projeto(projeto.id)
        assert resultado['tempo_total'] == approx(12.5)


@pytest.mark.django_db
class TestGetOverviewDataAll:

    def test_retorna_lista_vazia_sem_projetos_em_andamento(self):
        resultado = get_overview_data_all()
        assert resultado == []

    def test_nao_retorna_projetos_cancelados(self):
        baker.make('api.DimProjeto', status='Cancelado')
        resultado = get_overview_data_all()
        assert resultado == []

    def test_retorna_projetos_concluidos(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', status='Concluído', programa=programa)
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   custo_materiais=200.00)
        resultado = get_overview_data_all()
        assert len(resultado) > 0

    def test_retorna_dados_de_projeto_em_andamento(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', status='Em andamento', programa=programa)
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   custo_materiais=100.00)
        resultado = get_overview_data_all()
        assert len(resultado) > 0

    def test_estrutura_do_retorno(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', status='Em andamento', programa=programa)
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   custo_materiais=50.00)
        resultado = get_overview_data_all()
        assert 'date_str' in resultado[0]
        assert 'values' in resultado[0]

    def test_values_contem_campos_corretos(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', status='Em andamento', programa=programa)
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   custo_materiais=50.00)
        resultado = get_overview_data_all()
        value = resultado[0]['values'][0]
        assert 'codigo_projeto' in value
        assert 'nome_projeto' in value
        assert 'cost' in value

    def test_filtra_overview_por_programa_id(self):
        programa_a = baker.make('api.DimPrograma')
        programa_b = baker.make('api.DimPrograma')
        projeto_a = baker.make('api.DimProjeto', nome_projeto='Do A', status='Em andamento', programa=programa_a)
        projeto_b = baker.make('api.DimProjeto', nome_projeto='Do B', status='Em andamento', programa=programa_b)
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto_a, programa=programa_a,
                   material=material, fornecedor=fornecedor, tempo=tempo, custo_materiais=50.00)
        baker.make('api.FatoMateriais', projeto=projeto_b, programa=programa_b,
                   material=material, fornecedor=fornecedor, tempo=tempo, custo_materiais=75.00)

        resultado = get_overview_data_all(programa_id=programa_a.id)

        nomes = [v['nome_projeto'] for grupo in resultado for v in grupo['values']]
        assert 'Do A' in nomes
        assert 'Do B' not in nomes

    def test_overview_programa_id_none_retorna_todos(self):
        programa = baker.make('api.DimPrograma')
        projeto1 = baker.make('api.DimProjeto', status='Em andamento', programa=programa)
        projeto2 = baker.make('api.DimProjeto', status='Em andamento')
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto1, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo, custo_materiais=10.00)
        baker.make('api.FatoMateriais', projeto=projeto2, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo, custo_materiais=10.00)

        resultado = get_overview_data_all(programa_id=None)

        codigos = {v['codigo_projeto'] for grupo in resultado for v in grupo['values']}
        assert projeto1.codigo_projeto in codigos
        assert projeto2.codigo_projeto in codigos

    def test_overview_retorna_vazio_quando_programa_sem_projetos(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', status='Em andamento', programa=programa)
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo, custo_materiais=50.00)
        programa_vazio = baker.make('api.DimPrograma')

        resultado = get_overview_data_all(programa_id=programa_vazio.id)

        assert resultado == []


@pytest.mark.django_db
class TestGetMateriaisProjeto:

    def test_retorna_lista_vazia_quando_sem_empenhos(self):
        projeto = baker.make('api.DimProjeto')
        resultado = get_materiais_projeto(projeto.id)
        assert resultado['results'] == []
        assert resultado['count'] == 0

    def test_retorna_materiais_do_projeto(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        material = baker.make('api.DimMaterial', descricao='Capacitor', custo_estimado=10.00)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=5, custo_materiais=50.00)
        resultado = get_materiais_projeto(projeto.id)
        assert resultado['count'] == 1
        assert resultado['results'][0]['nome_material'] == 'Capacitor'

    def test_calcula_custo_total_corretamente(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        material = baker.make('api.DimMaterial', descricao='Resistor', custo_estimado=20.00)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=10, custo_materiais=200.00)
        resultado = get_materiais_projeto(projeto.id)
        assert resultado['results'][0]['custo_total_estimado'] == approx(200.0)

    def test_agrupa_empenhos_do_mesmo_material(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        material = baker.make('api.DimMaterial', descricao='Diodo', custo_estimado=5.00)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=10, custo_materiais=50.00)
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=20, custo_materiais=100.00)
        resultado = get_materiais_projeto(projeto.id)
        assert resultado['count'] == 1
        assert resultado['results'][0]['quantidade'] == 30

    def test_paginacao_retorna_page_size_correto(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        for i in range(15):
            material = baker.make('api.DimMaterial', descricao=f'Material {i}', custo_estimado=10.00)
            baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                       material=material, fornecedor=fornecedor, tempo=tempo,
                       quantidade_empenhada=1, custo_materiais=10.00)
        resultado = get_materiais_projeto(projeto.id, page=1, page_size=10)
        assert len(resultado['results']) == 10
        assert resultado['total_pages'] == 2

    def test_paginacao_segunda_pagina(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        for i in range(15):
            material = baker.make('api.DimMaterial', descricao=f'Material {i:02d}', custo_estimado=10.00)
            baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                       material=material, fornecedor=fornecedor, tempo=tempo,
                       quantidade_empenhada=1, custo_materiais=10.00)
        resultado = get_materiais_projeto(projeto.id, page=2, page_size=10)
        assert len(resultado['results']) == 5

    def test_nao_retorna_materiais_de_outro_projeto(self):
        programa = baker.make('api.DimPrograma')
        projeto1 = baker.make('api.DimProjeto', programa=programa)
        projeto2 = baker.make('api.DimProjeto', programa=programa)
        material = baker.make('api.DimMaterial', descricao='Transistor', custo_estimado=15.00)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto2, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=5, custo_materiais=75.00)
        resultado = get_materiais_projeto(projeto1.id)
        assert resultado['count'] == 0

    def test_filtra_materiais_por_periodo(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        material = baker.make('api.DimMaterial', descricao='Capacitor', custo_estimado=5.0)
        fornecedor = baker.make('api.DimFornecedor')
        tempo1 = baker.make('api.DimTempo', data=date(2025, 1, 1))
        tempo2 = baker.make('api.DimTempo', data=date(2025, 6, 1))
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo1,
                   quantidade_empenhada=5, custo_materiais=25.00)
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo2,
                   quantidade_empenhada=10, custo_materiais=50.00)
        resultado = get_materiais_projeto(projeto.id,
                                          data_inicio='2025-06-01', data_fim='2025-06-30')
        assert resultado['count'] == 1
        assert resultado['results'][0]['quantidade'] == 10

    def test_filtra_materiais_por_nome(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        capacitor = baker.make('api.DimMaterial', descricao='Capacitor', custo_estimado=5.0)
        resistor = baker.make('api.DimMaterial', descricao='Resistor', custo_estimado=3.0)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=capacitor, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=1, custo_materiais=5.00)
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=resistor, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=1, custo_materiais=3.00)
        resultado = get_materiais_projeto(projeto.id, material='cap')
        assert resultado['count'] == 1
        assert resultado['results'][0]['nome_material'] == 'Capacitor'


@pytest.mark.django_db
class TestGetMateriaisDisponiveis:

    def test_retorna_vazio_sem_empenhos(self):
        projeto = baker.make('api.DimProjeto')
        assert get_materiais_disponiveis(projeto.id) == []

    def test_retorna_materiais_empenhados_distintos(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        capacitor = baker.make('api.DimMaterial', descricao='Capacitor', custo_estimado=1.0)
        resistor = baker.make('api.DimMaterial', descricao='Resistor', custo_estimado=1.0)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=capacitor, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=1, custo_materiais=1.00)
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=capacitor, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=2, custo_materiais=2.00)
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=resistor, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=1, custo_materiais=1.00)
        resultado = get_materiais_disponiveis(projeto.id)
        descricoes = [m['descricao'] for m in resultado]
        assert descricoes == ['Capacitor', 'Resistor']

    def test_ignora_materiais_de_outro_projeto(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa)
        outro = baker.make('api.DimProjeto', programa=programa)
        material = baker.make('api.DimMaterial', descricao='Diodo', custo_estimado=1.0)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=outro, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=1, custo_materiais=1.00)
        assert get_materiais_disponiveis(projeto.id) == []


@pytest.mark.django_db
class TestGetMateriaisDisponiveisView:

    def test_retorna_200(self):
        projeto = baker.make('api.DimProjeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/materiais-disponiveis/')
        response = get_materiais_disponiveis_view(request, projeto.id)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/projetos/1/materiais-disponiveis/')
        response = get_materiais_disponiveis_view(request, 1)
        assert response.status_code == 405


@pytest.mark.django_db
class TestListarProjetosView:

    def test_retorna_200_para_get(self):
        factory = RequestFactory()
        request = factory.get('/projetos/')
        response = listar_projetos_view(request)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/projetos/')
        response = listar_projetos_view(request)
        assert response.status_code == 405

    def test_view_filtra_por_programa_id_na_query_string(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', nome_projeto='Do programa', programa=programa)
        baker.make('api.DimProjeto', nome_projeto='De outro programa')

        factory = RequestFactory()
        request = factory.get('/projetos/', {'programa_id': str(programa.id)})
        response = listar_projetos_view(request)

        import json
        data = json.loads(response.content)
        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]['nome_projeto'] == 'Do programa'

    def test_view_ignora_programa_id_invalido_e_retorna_todos(self):
        baker.make('api.DimProjeto', _quantity=2)

        factory = RequestFactory()
        request = factory.get('/projetos/', {'programa_id': 'abc'})
        response = listar_projetos_view(request)

        import json
        data = json.loads(response.content)
        assert response.status_code == 200
        assert len(data) == 2


@pytest.mark.django_db
class TestGetOverviewProjetosView:

    def test_retorna_200_para_get(self):
        factory = RequestFactory()
        request = factory.get('/projetos-overview/')
        response = get_overview_projetos(request)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/projetos-overview/')
        response = get_overview_projetos(request)
        assert response.status_code == 405

    def test_view_filtra_overview_por_programa_id(self):
        programa = baker.make('api.DimPrograma')
        outro_programa = baker.make('api.DimPrograma')
        projeto_do_programa = baker.make('api.DimProjeto', nome_projeto='Do programa', status='Em andamento', programa=programa)
        projeto_de_outro = baker.make('api.DimProjeto', nome_projeto='De outro', status='Em andamento', programa=outro_programa)
        material = baker.make('api.DimMaterial', custo_estimado=10.00)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto_do_programa, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo, custo_materiais=10.00)
        baker.make('api.FatoMateriais', projeto=projeto_de_outro, programa=outro_programa,
                   material=material, fornecedor=fornecedor, tempo=tempo, custo_materiais=10.00)

        factory = RequestFactory()
        request = factory.get('/projetos-overview/', {'programa_id': str(programa.id)})
        response = get_overview_projetos(request)

        import json
        data = json.loads(response.content)
        assert response.status_code == 200
        nomes = [v['nome_projeto'] for grupo in data for v in grupo['values']]
        assert 'Do programa' in nomes
        assert 'De outro' not in nomes

    def test_view_ignora_programa_id_invalido_no_overview(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', status='Em andamento', programa=programa)
        material = baker.make('api.DimMaterial', custo_estimado=10.00)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo, custo_materiais=10.00)

        factory = RequestFactory()
        request = factory.get('/projetos-overview/', {'programa_id': 'abc'})
        response = get_overview_projetos(request)

        import json
        data = json.loads(response.content)
        assert response.status_code == 200
        assert len(data) > 0


@pytest.mark.django_db
class TestGetResumoProjetoView:

    def test_retorna_200_para_projeto_existente(self):
        projeto = baker.make('api.DimProjeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/resumo/')
        response = get_resumo_projeto_view(request, projeto.id)
        assert response.status_code == 200

    def test_retorna_404_para_projeto_inexistente(self):
        factory = RequestFactory()
        request = factory.get('/projetos/99999/resumo/')
        response = get_resumo_projeto_view(request, 99999)
        assert response.status_code == 404

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/projetos/1/resumo/')
        response = get_resumo_projeto_view(request, 1)
        assert response.status_code == 405


@pytest.mark.django_db
class TestGetMateriaisProjetoView:

    def test_retorna_200_para_projeto_existente(self):
        projeto = baker.make('api.DimProjeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/materiais/')
        response = get_materiais_projeto_view(request, projeto.id)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/projetos/1/materiais/')
        response = get_materiais_projeto_view(request, 1)
        assert response.status_code == 405

    def test_retorna_estrutura_correta(self):
        projeto = baker.make('api.DimProjeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/materiais/')
        response = get_materiais_projeto_view(request, projeto.id)
        import json
        data = json.loads(response.content)
        assert 'count' in data
        assert 'page' in data
        assert 'total_pages' in data
        assert 'results' in data
