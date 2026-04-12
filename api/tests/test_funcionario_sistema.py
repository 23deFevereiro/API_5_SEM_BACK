import pytest
from django.urls import reverse
from model_bakery import baker


@pytest.fixture
def projeto():
    return baker.make('api.Projeto')


@pytest.mark.django_db
class TestFuncionariosProjetoSistema:

    def test_retorna_200_para_get(self, api_client, projeto):
        url = reverse('funcionarios_projeto', args=[projeto.id])

        response = api_client.get(url)

        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client, projeto):
        url = reverse('funcionarios_projeto', args=[projeto.id])

        response = api_client.post(url)

        assert response.status_code == 405

    def test_retorna_lista_vazia_quando_projeto_sem_tarefas(self, api_client, projeto):
        url = reverse('funcionarios_projeto', args=[projeto.id])

        response = api_client.get(url)
        data = response.json()

        assert data['count'] == 0
        assert data['results'] == []

    def test_retorna_estrutura_de_paginacao(self, api_client, projeto):
        url = reverse('funcionarios_projeto', args=[projeto.id])

        response = api_client.get(url)
        data = response.json()

        assert 'count' in data
        assert 'page' in data
        assert 'page_size' in data
        assert 'total_pages' in data
        assert 'results' in data

    def test_retorna_apenas_funcionarios_do_projeto_informado(self, api_client, projeto):
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make(
            'api.TempoTarefa',
            tarefa=tarefa,
            usuario='Alberto',
            horas_trabalhadas=8.0
        )

        url = reverse('funcionarios_projeto', args=[projeto.id])

        response = api_client.get(url)
        data = response.json()

        assert data['count'] == 1
        assert data['results'][0]['usuario'] == 'Alberto'

    def test_nao_retorna_funcionarios_de_outro_projeto(self, api_client, projeto):
        projeto2 = baker.make('api.Projeto')
        tarefa2 = baker.make('api.Tarefa', projeto=projeto2)

        baker.make(
            'api.TempoTarefa',
            tarefa=tarefa2,
            usuario='Carlos',
            horas_trabalhadas=6.0
        )

        url = reverse('funcionarios_projeto', args=[projeto.id])

        response = api_client.get(url)
        data = response.json()

        assert data['count'] == 0
        assert data['results'] == []

    def test_paginacao_funciona(self, api_client, projeto):
        tarefa = baker.make('api.Tarefa', projeto=projeto)

        for i in range(15):
            baker.make(
                'api.TempoTarefa',
                tarefa=tarefa,
                usuario=f'User{i}',
                horas_trabalhadas=1
            )

        url = reverse('funcionarios_projeto', args=[projeto.id])

        response = api_client.get(url, {'page': 2})
        data = response.json()

        assert data['page'] == 2
        assert data['total_pages'] == 2
        assert len(data['results']) > 0

    def test_nao_duplica_funcionarios(self, api_client, projeto):
        tarefa = baker.make('api.Tarefa', projeto=projeto)

        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Alberto', horas_trabalhadas=2)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Alberto', horas_trabalhadas=3)

        url = reverse('funcionarios_projeto', args=[projeto.id])

        response = api_client.get(url)
        data = response.json()

        assert data['count'] == 1