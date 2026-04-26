import pytest
from model_bakery import baker
from django.urls import reverse


@pytest.fixture
def projeto():
    return baker.make('api.Projeto')


@pytest.mark.django_db
class TestListarProjetosSistema:

    def test_retorna_200_para_get(self, api_client, projeto):
        url = reverse('listar_projetos')
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client):
        url = reverse('listar_projetos')
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_projetos(self, api_client):
        url = reverse('listar_projetos')
        response = api_client.get(url)
        assert response.json() == []

    def test_filtra_por_search(self, api_client):
        baker.make('api.Projeto', nome_projeto='Conversor DC-DC')
        baker.make('api.Projeto', nome_projeto='Driver LED')
        url = reverse('listar_projetos')
        response = api_client.get(url, {'search': 'Conversor'})
        data = response.json()
        assert len(data) == 1
        assert data[0]['nome_projeto'] == 'Conversor DC-DC'

    def test_filtra_por_programa_id(self, api_client):
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa, _quantity=2)
        baker.make('api.Projeto', _quantity=1)
        url = reverse('listar_projetos')
        response = api_client.get(url, {'programa_id': programa.id})
        assert len(response.json()) == 2

    def test_ignora_programa_id_invalido_e_retorna_todos(self, api_client):
        baker.make('api.Projeto', _quantity=2)
        url = reverse('listar_projetos')
        response = api_client.get(url, {'programa_id': 'abc'})
        assert response.status_code == 200
        assert len(response.json()) == 2


@pytest.mark.django_db
class TestOverviewProjetosSistema:

    def test_retorna_200_para_get(self, api_client):
        url = reverse('projetos_overview')
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client):
        url = reverse('projetos_overview')
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_projetos_em_andamento(self, api_client):
        baker.make('api.Projeto', status='Concluido')
        url = reverse('projetos_overview')
        response = api_client.get(url)
        assert response.json() == []

    def test_filtra_por_programa_id(self, api_client):
        programa = baker.make('api.Programa')
        projeto_do_programa = baker.make('api.Projeto', status='Em andamento', programa=programa)
        projeto_outro = baker.make('api.Projeto', status='Em andamento')
        material = baker.make('api.Material', custo_estimado=10.00)
        baker.make('api.EmpenhoMaterial', projeto=projeto_do_programa, material=material, quantidade_empenhada=1)
        baker.make('api.EmpenhoMaterial', projeto=projeto_outro, material=material, quantidade_empenhada=1)
        url = reverse('projetos_overview')
        response = api_client.get(url, {'programa_id': programa.id})
        data = response.json()
        assert response.status_code == 200
        nomes = [v['nome_projeto'] for grupo in data for v in grupo['values']]
        assert projeto_do_programa.nome_projeto in nomes
        assert projeto_outro.nome_projeto not in nomes


@pytest.mark.django_db
class TestResumoProjetoSistema:

    def test_retorna_200_para_projeto_existente(self, api_client, projeto):
        url = reverse('resumo_projeto', args=[projeto.id])
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_404_para_projeto_inexistente(self, api_client):
        url = reverse('resumo_projeto', args=[99999])
        response = api_client.get(url)
        assert response.status_code == 404

    def test_retorna_405_para_post(self, api_client, projeto):
        url = reverse('resumo_projeto', args=[projeto.id])
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_estrutura_correta(self, api_client, projeto):
        url = reverse('resumo_projeto', args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert 'custo_total' in data
        assert 'tempo_total' in data


@pytest.mark.django_db
class TestMateriaisProjetoSistema:

    def test_retorna_200_para_projeto_existente(self, api_client, projeto):
        url = reverse('materiais_projeto', args=[projeto.id])
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client, projeto):
        url = reverse('materiais_projeto', args=[projeto.id])
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_estrutura_correta(self, api_client, projeto):
        url = reverse('materiais_projeto', args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert 'count' in data
        assert 'page' in data
        assert 'total_pages' in data
        assert 'results' in data

    def test_retorna_lista_vazia_sem_empenhos(self, api_client, projeto):
        url = reverse('materiais_projeto', args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert data['count'] == 0
        assert data['results'] == []


@pytest.mark.django_db
class TestMateriaisDisponiveisSistema:

    def test_retorna_200_para_projeto_existente(self, api_client, projeto):
        url = reverse('materiais_disponiveis_projeto', args=[projeto.id])
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client, projeto):
        url = reverse('materiais_disponiveis_projeto', args=[projeto.id])
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_empenhos(self, api_client, projeto):
        url = reverse('materiais_disponiveis_projeto', args=[projeto.id])
        response = api_client.get(url)
        assert response.json() == []

    def test_retorna_materiais_do_projeto(self, api_client, projeto):
        material = baker.make('api.Material', descricao='Capacitor')
        baker.make('api.EmpenhoMaterial', projeto=projeto, material=material, quantidade_empenhada=1)
        url = reverse('materiais_disponiveis_projeto', args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1
        assert data[0]['descricao'] == 'Capacitor'