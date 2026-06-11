from unittest.mock import patch

import pytest
from django.urls import reverse
from model_bakery import baker


@pytest.fixture
def projeto():
    return baker.make("api.DimProjeto", id=1)


@pytest.mark.django_db
class TestListarProjetosSistema:

    # TC-P01 — Status 200 no endpoint GET /api/projetos/
    def test_retorna_200_para_get(self, api_client, projeto):
        url = reverse("listar_projetos")
        response = api_client.get(url)
        assert response.status_code == 200

    # Complementar ao TC-P01: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client):
        url = reverse("listar_projetos")
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-P01 — Cenário: Nenhum projeto cadastrado (body [])
    def test_retorna_lista_vazia_sem_projetos(self, api_client):
        url = reverse("listar_projetos")
        response = api_client.get(url)
        assert response.json() == []

    # TC-P01 — Cenário: Filtrar projetos por texto via search
    def test_filtra_por_search(self, api_client):
        baker.make("api.DimProjeto", nome_projeto="Conversor DC-DC")
        baker.make("api.DimProjeto", nome_projeto="Driver LED")
        url = reverse("listar_projetos")
        response = api_client.get(url, {"search": "Conversor"})
        data = response.json()
        assert len(data) == 1
        assert data[0]["nome_projeto"] == "Conversor DC-DC"

    # TC-P01 — Cenário: Filtrar projetos por programa
    def test_filtra_por_programa_id(self, api_client):
        programa = baker.make("api.DimPrograma")
        baker.make("api.DimProjeto", programa=programa, _quantity=2)
        baker.make("api.DimProjeto", _quantity=1)
        url = reverse("listar_projetos")
        response = api_client.get(url, {"programa_id": programa.id})
        assert len(response.json()) == 2

    # Complementar ao TC-P01: programa_id inválido é ignorado e retorna todos
    def test_ignora_programa_id_invalido_e_retorna_todos(self, api_client):
        baker.make("api.DimProjeto", _quantity=2)
        url = reverse("listar_projetos")
        response = api_client.get(url, {"programa_id": "abc"})
        assert response.status_code == 200
        assert len(response.json()) == 2

    # TC-P01 — Cenário: Search sem correspondência (body [])
    def test_search_sem_correspondencia_retorna_lista_vazia(self, api_client):
        baker.make("api.DimProjeto", nome_projeto="Conversor DC-DC")
        url = reverse("listar_projetos")
        response = api_client.get(url, {"search": "xyzinexistente"})
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.django_db
class TestOverviewProjetosSistema:

    # TC-P02 — Status 200 no endpoint GET /api/projetos-overview
    def test_retorna_200_para_get(self, api_client):
        url = reverse("projetos_overview")
        response = api_client.get(url)
        assert response.status_code == 200

    # Complementar ao TC-P02: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client):
        url = reverse("projetos_overview")
        response = api_client.post(url)
        assert response.status_code == 405

    # Complementar ao TC-P02: projetos cancelados ficam fora do overview
    def test_nao_retorna_projetos_cancelados(self, api_client):
        baker.make("api.DimProjeto", status="Cancelado")
        url = reverse("projetos_overview")
        response = api_client.get(url)
        assert response.json() == []

    # TC-P02 — Cenário: Filtrar por programa_id
    def test_filtra_por_programa_id(self, api_client):
        programa = baker.make("api.DimPrograma")
        projeto_do_programa = baker.make(
            "api.DimProjeto", status="Em andamento", programa=programa
        )
        projeto_outro = baker.make("api.DimProjeto", status="Em andamento")
        material = baker.make("api.DimMaterial", custo_estimado=10.00)
        tempo = baker.make(
            "api.DimTempo",
            id=20230101,
            data="2023-01-01",
            ano=2023,
            mes=1,
            trimestre=1,
            semestre=1,
            dia_semana=0,
        )
        baker.make(
            "api.FatoMateriais",
            projeto=projeto_do_programa,
            programa=programa,
            material=material,
            tempo=tempo,
            quantidade_empenhada=1,
        )
        baker.make(
            "api.FatoMateriais",
            projeto=projeto_outro,
            material=material,
            tempo=tempo,
            quantidade_empenhada=1,
        )
        url = reverse("projetos_overview")
        response = api_client.get(url, {"programa_id": programa.id})
        data = response.json()
        assert response.status_code == 200
        nomes = [v["nome_projeto"] for grupo in data for v in grupo["values"]]
        assert projeto_do_programa.nome_projeto in nomes
        assert projeto_outro.nome_projeto not in nomes


@pytest.mark.django_db
class TestResumoProjetoSistema:

    # TC-P03 — Cenário: Retornar resumo de projeto existente (status 200)
    def test_retorna_200_para_projeto_existente(self, api_client, projeto):
        url = reverse("resumo_projeto", args=[projeto.id])
        response = api_client.get(url)
        assert response.status_code == 200

    # TC-P03 — Cenário: Projeto inexistente
    # (404 + body {'error': 'Projeto não encontrado'})
    def test_retorna_404_para_projeto_inexistente(self, api_client):
        url = reverse("resumo_projeto", args=[99999])
        response = api_client.get(url)
        assert response.status_code == 404
        assert response.json() == {"error": "Projeto não encontrado"}

    # TC-P03 — Cenário: projeto_id não numérico (404 pelo roteamento <int> do Django)
    def test_retorna_404_para_projeto_id_nao_numerico(self, api_client):
        # O conversor <int:projeto_id> da URL rejeita texto antes da view
        response = api_client.get("/api/projetos/abc/resumo/")
        assert response.status_code == 404

    # Complementar ao TC-P03: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client, projeto):
        url = reverse("resumo_projeto", args=[projeto.id])
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-P03 — Contrato: body com custo_total e tempo_total
    def test_retorna_estrutura_correta(self, api_client, projeto):
        url = reverse("resumo_projeto", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert "custo_total" in data
        assert "tempo_total" in data


@pytest.mark.django_db
class TestMateriaisProjetoSistema:

    # TC-P04 — Status 200 para projeto existente
    def test_retorna_200_para_projeto_existente(self, api_client, projeto):
        url = reverse("materiais_projeto", args=[projeto.id])
        response = api_client.get(url)
        assert response.status_code == 200

    # Complementar ao TC-P04: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client, projeto):
        url = reverse("materiais_projeto", args=[projeto.id])
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-P04 — Contrato paginado (count, page, total_pages, results)
    def test_retorna_estrutura_correta(self, api_client, projeto):
        url = reverse("materiais_projeto", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert "count" in data
        assert "page" in data
        assert "total_pages" in data
        assert "results" in data

    # Complementar ao TC-P04: projeto sem materiais retorna count=0 e results=[]
    def test_retorna_lista_vazia_sem_empenhos(self, api_client, projeto):
        url = reverse("materiais_projeto", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert data["count"] == 0
        assert data["results"] == []

    # TC-P04 — Cenário: Projeto inexistente
    # (404 + body {'error': 'Projeto não encontrado'})
    def test_retorna_404_para_projeto_inexistente(self, api_client):
        url = reverse("materiais_projeto", args=[9999])
        response = api_client.get(url)
        assert response.status_code == 404
        assert response.json() == {"error": "Projeto não encontrado"}


@pytest.mark.django_db
class TestMateriaisDisponiveisSistema:

    # Fora da especificação: endpoint auxiliar /materiais-disponiveis/
    def test_retorna_200_para_projeto_existente(self, api_client, projeto):
        url = reverse("materiais_disponiveis_projeto", args=[projeto.id])
        response = api_client.get(url)
        assert response.status_code == 200

    # Fora da especificação: endpoint auxiliar /materiais-disponiveis/
    def test_retorna_405_para_post(self, api_client, projeto):
        url = reverse("materiais_disponiveis_projeto", args=[projeto.id])
        response = api_client.post(url)
        assert response.status_code == 405

    # Fora da especificação: endpoint auxiliar /materiais-disponiveis/
    def test_retorna_lista_vazia_sem_empenhos(self, api_client, projeto):
        url = reverse("materiais_disponiveis_projeto", args=[projeto.id])
        response = api_client.get(url)
        assert response.json() == []

    # Fora da especificação: endpoint auxiliar /materiais-disponiveis/
    def test_retorna_materiais_do_projeto(self, api_client, projeto):
        material = baker.make("api.DimMaterial", descricao="Capacitor")
        baker.make(
            "api.FatoMateriais",
            projeto=projeto,
            material=material,
            quantidade_empenhada=1,
        )
        url = reverse("materiais_disponiveis_projeto", args=[projeto.id])
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1


@pytest.mark.django_db
class TestProjetoErrosSistema:

    # Fora da especificação: erro interno (500) no resumo do projeto
    def test_resumo_retorna_500_quando_service_levanta_excecao(
        self, api_client, projeto
    ):
        url = reverse("resumo_projeto", args=[projeto.id])
        with patch(
            "api.views.projeto_view.get_resumo_projeto",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500

    # TC-P04 — Cenário: data_inicio em formato inválido
    # (400 + mensagem de erro da especificação)
    def test_materiais_retorna_400_para_data_invalida(self, api_client, projeto):
        url = reverse("materiais_projeto", args=[projeto.id])
        response = api_client.get(url, {"data_inicio": "31-01-2026"})
        assert response.status_code == 400
        assert response.json() == {
            "error": "Formato inválido para 'data_inicio': esperado YYYY-MM-DD"
        }

    # Fora da especificação: erro interno (500) nos materiais do projeto
    def test_materiais_retorna_500_quando_service_levanta_excecao(
        self, api_client, projeto
    ):
        url = reverse("materiais_projeto", args=[projeto.id])
        with patch(
            "api.views.projeto_view.get_materiais_projeto",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500

    # Fora da especificação: erro interno (500) no endpoint auxiliar
    def test_materiais_disponiveis_retorna_500_quando_service_levanta_excecao(
        self, api_client, projeto
    ):
        url = reverse("materiais_disponiveis_projeto", args=[projeto.id])
        with patch(
            "api.views.projeto_view.get_materiais_disponiveis",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500
