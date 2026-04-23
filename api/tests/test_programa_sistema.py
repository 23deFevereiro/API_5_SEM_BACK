import pytest
from model_bakery import baker
from django.test import RequestFactory
from api.views.programa_view import listar_programas_view, get_resumo_programa_view


@pytest.mark.django_db
class TestListarProgramasView:

    def test_retorna_200_para_get(self):
        factory = RequestFactory()
        request = factory.get('/programas/')
        response = listar_programas_view(request)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/programas/')
        response = listar_programas_view(request)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_programas(self):
        import json
        factory = RequestFactory()
        request = factory.get('/programas/')
        response = listar_programas_view(request)
        data = json.loads(response.content)
        assert data == []

    def test_retorna_programas_cadastrados(self, api_client):
        baker.make('api.DimPrograma', nome_programa='Naval')
        baker.make('api.DimPrograma', nome_programa='Aeroespacial')

        url = reverse('listar_programas')

        response = api_client.get(url)
        data = response.json()

        nomes = [p['nome'] for p in data]
        assert len(data) == 2
        assert 'Naval' in nomes
        assert 'Aeroespacial' in nomes

    def test_filtra_por_search(self, api_client):
        baker.make('api.DimPrograma', nome_programa='Naval')
        baker.make('api.DimPrograma', nome_programa='Aeroespacial')

        url = reverse('listar_programas')

        response = api_client.get(url, {'search': 'Nav'})
        data = response.json()

        assert len(data) == 1


@pytest.mark.django_db
class TestGetResumoProgramaView:

    def test_endpoint_filtra_projetos_por_programa_id(self, api_client):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', nome_projeto='Do programa', programa=programa)
        baker.make('api.DimProjeto', nome_projeto='De outro programa')

        url = reverse('listar_projetos')

        response = api_client.get(url, {'programa_id': programa.id})
        data = response.json()

        assert response.status_code == 200

    def test_endpoint_sem_programa_id_retorna_todos(self, api_client):
        baker.make('api.DimProjeto', _quantity=3)

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/programas/1/resumo/')
        response = get_resumo_programa_view(request, 1)
        assert response.status_code == 405

        response = api_client.get(url)
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 3

    def test_endpoint_aceita_programa_id_junto_com_search(self, api_client):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', nome_projeto='Conversor DC-DC', programa=programa)
        baker.make('api.DimProjeto', nome_projeto='Driver LED', programa=programa)
        baker.make('api.DimProjeto', nome_projeto='Conversor AC')

        url = reverse('listar_projetos')

        response = api_client.get(url, {'programa_id': programa.id, 'search': 'Conversor'})
        data = response.json()

        assert len(data) == 1
        assert data[0]['nome_projeto'] == 'Conversor DC-DC'


@pytest.mark.django_db
class TestOverviewProjetosFiltroProgramaSistema:

    def test_overview_filtra_por_programa_id(self, api_client):
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

        url = reverse('projetos_overview')

        response = api_client.get(url, {'programa_id': programa.id})
        data = response.json()

        assert response.status_code == 200
        nomes = [v['nome_projeto'] for grupo in data for v in grupo['values']]
        assert 'Do programa' in nomes
        assert 'De outro' not in nomes

    def test_overview_sem_programa_id_retorna_todos(self, api_client):
        programa = baker.make('api.DimPrograma')
        projeto1 = baker.make('api.DimProjeto', status='Em andamento', programa=programa)
        projeto2 = baker.make('api.DimProjeto', status='Em andamento', programa=programa)
        material = baker.make('api.DimMaterial', custo_estimado=10.00)
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', projeto=projeto1, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo, custo_materiais=10.00)
        baker.make('api.FatoMateriais', projeto=projeto2, programa=programa,
                   material=material, fornecedor=fornecedor, tempo=tempo, custo_materiais=10.00)

        url = reverse('projetos_overview')

        response = api_client.get(url)
        data = response.json()

        codigos = {v['codigo_projeto'] for grupo in data for v in grupo['values']}
        assert projeto1.codigo_projeto in codigos
        assert projeto2.codigo_projeto in codigos
