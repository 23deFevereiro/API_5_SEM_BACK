from datetime import date
from unittest.mock import patch

import pytest
from django.urls import reverse
from model_bakery import baker
from pytest import approx


def make_fato_horas(
    projeto, funcionario, horas, tempo=None, programa=None, tarefa=None
):
    if programa is None:
        programa = baker.make("api.DimPrograma")
    if tempo is None:
        tempo = baker.make("api.DimTempo")
    if tarefa is None:
        tarefa = baker.make("api.DimTarefa", projeto=projeto)
    return baker.make(
        "api.FatoHoras",
        projeto=projeto,
        programa=programa,
        funcionario=funcionario,
        tarefa=tarefa,
        tempo=tempo,
        horas_trabalhadas=horas,
        custo_horas=0,
    )


@pytest.fixture
def projeto():
    return baker.make("api.DimProjeto", id=1)


@pytest.mark.django_db
class TestHorasPorFuncionarioSistema:

    # TC-P05 — Status 200 no endpoint GET /api/projetos/{id}/horas-por-funcionario/
    def test_retorna_200_para_get(self, api_client, projeto):
        url = reverse("horas_por_funcionario", args=[projeto.id])
        response = api_client.get(url)
        assert response.status_code == 200

    # Complementar ao TC-P05: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client, projeto):
        url = reverse("horas_por_funcionario", args=[projeto.id])
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-P05 — Cenário: Projeto sem horas registradas (body [])
    def test_retorna_lista_vazia_sem_dados(self, api_client, projeto):
        url = reverse("horas_por_funcionario", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert data == []

    # TC-P05 — Cenário: Retornar horas consolidadas por funcionário
    def test_retorna_horas_de_um_funcionario(self, api_client, projeto):
        funcionario = baker.make("api.DimFuncionario", nome="Ana")
        make_fato_horas(projeto, funcionario, horas=6.0)
        url = reverse("horas_por_funcionario", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1
        assert data[0]["funcionario"] == "Ana"
        assert data[0]["total_horas"] == approx(6.0)

    # TC-P05 — Cenário: Retornar horas consolidadas (agregação de registros)
    def test_agrega_multiplos_registros(self, api_client, projeto):
        funcionario = baker.make("api.DimFuncionario", nome="Carlos")
        tempo = baker.make("api.DimTempo", data=date(2025, 1, 1))
        make_fato_horas(projeto, funcionario, horas=4.0, tempo=tempo)
        make_fato_horas(projeto, funcionario, horas=3.0, tempo=tempo)
        url = reverse("horas_por_funcionario", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1
        assert data[0]["total_horas"] == approx(7.0)

    # Complementar ao TC-P05: horas de outro projeto não vazam
    def test_nao_mistura_projetos(self, api_client, projeto):
        projeto2 = baker.make("api.DimProjeto", id=2)
        ana = baker.make("api.DimFuncionario", nome="Ana")
        carlos = baker.make("api.DimFuncionario", nome="Carlos")
        tempo = baker.make("api.DimTempo", data=date(2025, 1, 1))
        make_fato_horas(projeto, ana, horas=8.0, tempo=tempo)
        make_fato_horas(projeto2, carlos, horas=5.0, tempo=tempo)
        url = reverse("horas_por_funcionario", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1
        assert data[0]["funcionario"] == "Ana"

    # TC-P05 — Cenário: Retornar horas consolidadas (múltiplos funcionários)
    def test_retorna_multiplos_funcionarios(self, api_client, projeto):
        ana = baker.make("api.DimFuncionario", nome="Ana")
        bruno = baker.make("api.DimFuncionario", nome="Bruno")
        tempo = baker.make("api.DimTempo", data=date(2025, 1, 1))
        make_fato_horas(projeto, ana, horas=4.0, tempo=tempo)
        make_fato_horas(projeto, bruno, horas=6.0, tempo=tempo)
        url = reverse("horas_por_funcionario", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 2
        usuarios = [r["funcionario"] for r in data]
        assert "Ana" in usuarios
        assert "Bruno" in usuarios


@pytest.mark.django_db
class TestHorasFuncionarioErrosSistema:

    # Complementar ao TC-P05: data_inicio inválida retorna 400
    def test_retorna_400_para_data_invalida(self, api_client, projeto):
        url = reverse("horas_por_funcionario", args=[projeto.id])
        response = api_client.get(url, {"data_inicio": "31-13-9999"})
        assert response.status_code == 400

    # TC-P05 — Cenário: data_fim em formato inválido (400 + mensagem de erro da especificação)
    def test_retorna_400_para_data_fim_invalida(self, api_client, projeto):
        url = reverse("horas_por_funcionario", args=[projeto.id])
        response = api_client.get(url, {"data_fim": "2026/01/31"})
        assert response.status_code == 400
        assert response.json() == {
            "error": "Formato inválido para 'data_fim': esperado YYYY-MM-DD"
        }

    # Fora da especificação: erro interno (500)
    def test_retorna_500_quando_service_levanta_excecao(self, api_client, projeto):
        url = reverse("horas_por_funcionario", args=[projeto.id])
        with patch(
            "api.views.horas_view.get_horas_por_funcionario",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500


@pytest.mark.django_db
class TestBurnupHorasProjetosErrosSistema:

    # Fora da especificação: erro interno (500) no burnup de horas (TC-P07)
    def test_retorna_500_quando_service_levanta_excecao(self, api_client):
        url = reverse("burnup_horas_projetos")
        with patch(
            "api.views.horas_view.get_burnup_horas_projetos",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500


@pytest.mark.django_db
class TestNomesFuncionariosErrosSistema:

    # Fora da especificação: endpoint auxiliar /nomes-funcionarios/
    def test_retorna_500_quando_service_levanta_excecao(self, api_client, projeto):
        url = reverse("nomes_funcionarios_projeto", args=[projeto.id])
        with patch(
            "api.views.horas_view.get_nomes_funcionarios_projeto",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500
