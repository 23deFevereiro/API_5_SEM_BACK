from datetime import date
from unittest.mock import patch

import pytest
from django.urls import reverse
from model_bakery import baker


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
class TestFuncionariosProjetoSistema:

    # TC-P06 — Status 200 no endpoint GET /api/projetos/{id}/funcionarios/
    def test_retorna_200_para_get(self, api_client, projeto):
        url = reverse("funcionarios_projeto", args=[projeto.id])
        response = api_client.get(url)
        assert response.status_code == 200

    # Complementar ao TC-P06: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client, projeto):
        url = reverse("funcionarios_projeto", args=[projeto.id])
        response = api_client.post(url)
        assert response.status_code == 405

    # Complementar ao TC-P06: projeto sem dados retorna count=0 e results=[]
    def test_retorna_lista_vazia_quando_projeto_sem_dados(self, api_client, projeto):
        url = reverse("funcionarios_projeto", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert data["count"] == 0
        assert data["results"] == []

    # TC-P06 — Contrato paginado (count, page, page_size, total_pages, results)
    def test_retorna_estrutura_de_paginacao(self, api_client, projeto):
        url = reverse("funcionarios_projeto", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert "count" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "results" in data

    # TC-P06 — Cenário: Retornar funcionários com horas e projetos
    def test_retorna_apenas_funcionarios_do_projeto_informado(
        self, api_client, projeto
    ):
        funcionario = baker.make("api.DimFuncionario", nome="Alberto")
        make_fato_horas(projeto, funcionario, horas=8.0)
        url = reverse("funcionarios_projeto", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["funcionario"] == "Alberto"

    # Complementar ao TC-P06: funcionários de outro projeto não vazam
    def test_nao_retorna_funcionarios_de_outro_projeto(self, api_client, projeto):
        projeto2 = baker.make("api.DimProjeto", id=2)
        carlos = baker.make("api.DimFuncionario", nome="Carlos")
        make_fato_horas(projeto2, carlos, horas=6.0)
        url = reverse("funcionarios_projeto", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert data["count"] == 0
        assert data["results"] == []

    # TC-P06 — Contrato paginado (page=2 com 15 funcionários)
    def test_paginacao_funciona(self, api_client, projeto):
        tempo = baker.make("api.DimTempo", data=date(2025, 1, 1))
        for i in range(15):
            f = baker.make("api.DimFuncionario", nome=f"User{i}")
            make_fato_horas(projeto, f, horas=1, tempo=tempo)
        url = reverse("funcionarios_projeto", args=[projeto.id])
        response = api_client.get(url, {"page": 2})
        data = response.json()
        assert data["page"] == 2
        assert data["total_pages"] == 2
        assert len(data["results"]) > 0

    # Complementar ao TC-P06: registros do mesmo funcionário são agregados
    def test_nao_duplica_funcionarios(self, api_client, projeto):
        funcionario = baker.make("api.DimFuncionario", nome="Alberto")
        tempo = baker.make("api.DimTempo", data=date(2025, 1, 1))
        make_fato_horas(projeto, funcionario, horas=2, tempo=tempo)
        make_fato_horas(projeto, funcionario, horas=3, tempo=tempo)
        url = reverse("funcionarios_projeto", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert data["count"] == 1


@pytest.mark.django_db
class TestFuncionariosProjetoErrosSistema:

    # TC-P06 — Cenário: data_inicio inválida (400 + mensagem de erro da especificação)
    def test_retorna_400_para_data_invalida(self, api_client, projeto):
        url = reverse("funcionarios_projeto", args=[projeto.id])
        response = api_client.get(url, {"data_inicio": "abc"})
        assert response.status_code == 400
        assert response.json() == {
            "error": "Formato inválido para 'data_inicio': esperado YYYY-MM-DD"
        }

    # Fora da especificação: erro interno (500)
    def test_retorna_500_quando_service_levanta_excecao(self, api_client, projeto):
        url = reverse("funcionarios_projeto", args=[projeto.id])
        with patch(
            "api.views.funcionario_view.get_funcionarios_projeto",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500
