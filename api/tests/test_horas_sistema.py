import pytest
from pytest import approx
from model_bakery import baker
from django.urls import reverse


@pytest.fixture
def projeto():
    return baker.make('api.Projeto')


@pytest.mark.django_db
class TestHorasPorFuncionarioSistema:

    def test_retorna_200_para_get(self, api_client, projeto):
        url = reverse('horas_por_funcionario', args=[projeto.id])

        response = api_client.get(url)

        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client, projeto):
        url = reverse('horas_por_funcionario', args=[projeto.id])

        response = api_client.post(url)

        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_dados(self, api_client, projeto):
        url = reverse('horas_por_funcionario', args=[projeto.id])

        response = api_client.get(url)
        data = response.json()

        assert data == []

    def test_retorna_horas_de_um_funcionario(self, api_client, projeto):
        tarefa = baker.make('api.Tarefa', projeto=projeto)

        baker.make(
            'api.TempoTarefa',
            tarefa=tarefa,
            usuario='Ana',
            horas_trabalhadas=6.0
        )

        url = reverse('horas_por_funcionario', args=[projeto.id])

        response = api_client.get(url)
        data = response.json()

        assert len(data) == 1
        assert data[0]['funcionario'] == 'Ana'
        assert data[0]['total_horas'] == approx(6.0)

    def test_agrega_multiplos_registros(self, api_client, projeto):
        tarefa = baker.make('api.Tarefa', projeto=projeto)

        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Carlos', horas_trabalhadas=4.0)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Carlos', horas_trabalhadas=3.0)

        url = reverse('horas_por_funcionario', args=[projeto.id])

        response = api_client.get(url)
        data = response.json()

        assert len(data) == 1
        assert data[0]['total_horas'] == approx(7.0)

    def test_nao_mistura_projetos(self, api_client, projeto):
        projeto2 = baker.make('api.Projeto')

        tarefa1 = baker.make('api.Tarefa', projeto=projeto)
        tarefa2 = baker.make('api.Tarefa', projeto=projeto2)

        baker.make('api.TempoTarefa', tarefa=tarefa1, usuario='Ana', horas_trabalhadas=8.0)
        baker.make('api.TempoTarefa', tarefa=tarefa2, usuario='Carlos', horas_trabalhadas=5.0)

        url = reverse('horas_por_funcionario', args=[projeto.id])

        response = api_client.get(url)
        data = response.json()

        assert len(data) == 1
        assert data[0]['funcionario'] == 'Ana'

    def test_retorna_multiplos_funcionarios(self, api_client, projeto):
        tarefa = baker.make('api.Tarefa', projeto=projeto)

        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Ana', horas_trabalhadas=4.0)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Bruno', horas_trabalhadas=6.0)

        url = reverse('horas_por_funcionario', args=[projeto.id])

        response = api_client.get(url)
        data = response.json()

        assert len(data) == 2

        usuarios = [r['funcionario'] for r in data]
        assert 'Ana' in usuarios
        assert 'Bruno' in usuarios