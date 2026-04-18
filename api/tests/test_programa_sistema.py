import pytest
from model_bakery import baker
from django.urls import reverse


@pytest.mark.django_db
class TestListarProgramasSistema:

    def test_retorna_200_para_get(self, api_client):
        url = reverse('listar_programas')

        response = api_client.get(url)

        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client):
        url = reverse('listar_programas')

        response = api_client.post(url)

        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_programas(self, api_client):
        url = reverse('listar_programas')

        response = api_client.get(url)
        data = response.json()

        assert data == []

    def test_retorna_programas_cadastrados(self, api_client):
        baker.make('api.Programa', nome_programa='Naval')
        baker.make('api.Programa', nome_programa='Aeroespacial')

        url = reverse('listar_programas')

        response = api_client.get(url)
        data = response.json()

        nomes = [p['nome'] for p in data]
        assert len(data) == 2
        assert 'Naval' in nomes
        assert 'Aeroespacial' in nomes

    def test_filtra_por_search(self, api_client):
        baker.make('api.Programa', nome_programa='Naval')
        baker.make('api.Programa', nome_programa='Aeroespacial')

        url = reverse('listar_programas')

        response = api_client.get(url, {'search': 'Nav'})
        data = response.json()

        assert len(data) == 1
        assert data[0]['nome'] == 'Naval'


@pytest.mark.django_db
class TestListarProjetosFiltroProgramaSistema:

    def test_endpoint_filtra_projetos_por_programa_id(self, api_client):
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', nome_projeto='Do programa', programa=programa)
        baker.make('api.Projeto', nome_projeto='De outro programa')

        url = reverse('listar_projetos')

        response = api_client.get(url, {'programa_id': programa.id})
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]['nome_projeto'] == 'Do programa'

    def test_endpoint_sem_programa_id_retorna_todos(self, api_client):
        baker.make('api.Projeto', _quantity=3)

        url = reverse('listar_projetos')

        response = api_client.get(url)
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 3

    def test_endpoint_aceita_programa_id_junto_com_search(self, api_client):
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', nome_projeto='Conversor DC-DC', programa=programa)
        baker.make('api.Projeto', nome_projeto='Driver LED', programa=programa)
        baker.make('api.Projeto', nome_projeto='Conversor AC')

        url = reverse('listar_projetos')

        response = api_client.get(url, {'programa_id': programa.id, 'search': 'Conversor'})
        data = response.json()

        assert len(data) == 1
        assert data[0]['nome_projeto'] == 'Conversor DC-DC'
