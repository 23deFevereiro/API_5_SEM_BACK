import pytest
from model_bakery import baker
from django.urls import reverse


@pytest.fixture
def programa():
    return baker.make('api.Programa')


@pytest.mark.django_db
class TestListarProgramasSistema:

    def test_retorna_200_para_get(self, api_client, programa):
        url = reverse('listar_programas')
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse('listar_programas')
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_programas(self, api_client):
        url = reverse('listar_programas')
        response = api_client.get(url)
        assert response.json() == []

    def test_filtra_por_search(self, api_client):
        baker.make('api.Programa', nome_programa='Programa Alpha')
        baker.make('api.Programa', nome_programa='Programa Beta')
        url = reverse('listar_programas')
        response = api_client.get(url, {'search': 'Alpha'})
        assert len(response.json()) == 1


@pytest.mark.django_db
class TestResumoProgramaSistema:

    def test_retorna_200_para_programa_existente(self, api_client, programa):
        url = reverse('resumo_programa', args=[programa.id])
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_404_para_programa_inexistente(self, api_client):
        url = reverse('resumo_programa', args=[99999])
        response = api_client.get(url)
        assert response.status_code == 404

    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse('resumo_programa', args=[programa.id])
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_estrutura_correta(self, api_client, programa):
        url = reverse('resumo_programa', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert 'total_projetos' in data
        assert 'horas_estimadas' in data
        assert 'horas_realizadas' in data
        assert 'custo_estimado' in data
        assert 'custo_real' in data


@pytest.mark.django_db
class TestDistribuicaoStatusSistema:

    def test_retorna_200_para_programa_existente(self, api_client, programa):
        url = reverse('distribuicao_status', args=[programa.id])
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse('distribuicao_status', args=[programa.id])
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_estrutura_correta(self, api_client, programa):
        url = reverse('distribuicao_status', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert 'total' in data
        assert 'status' in data

    def test_retorna_vazio_sem_projetos(self, api_client, programa):
        url = reverse('distribuicao_status', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data['total'] == 0
        assert data['status'] == []

    def test_retorna_dados_corretos_com_projetos(self, api_client, programa):
        baker.make('api.Projeto', programa=programa, status='Planejamento', _quantity=3)
        baker.make('api.Projeto', programa=programa, status='Concluído', _quantity=2)
        url = reverse('distribuicao_status', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data['total'] == 5
        assert len(data['status']) == 2
