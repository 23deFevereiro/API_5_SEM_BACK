from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from model_bakery import baker


@pytest.fixture
def programa():
    return baker.make("api.DimPrograma", id=1)


@pytest.mark.django_db
class TestListarProgramasSistema:

    # TC-PR01 — Status 200 no endpoint GET /api/programas/
    def test_retorna_200_para_get(self, api_client, programa):
        url = reverse("listar_programas")
        response = api_client.get(url)
        assert response.status_code == 200

    # Complementar ao TC-PR01: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse("listar_programas")
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-PR01 — Cenário: Nenhum programa cadastrado (body [])
    def test_retorna_lista_vazia_sem_programas(self, api_client):
        url = reverse("listar_programas")
        response = api_client.get(url)
        assert response.json() == []

    # TC-PR01 — Cenário: Filtrar por search
    def test_filtra_por_search(self, api_client):
        baker.make("api.DimPrograma", nome_programa="Programa Alpha")
        baker.make("api.DimPrograma", nome_programa="Programa Beta")
        url = reverse("listar_programas")
        response = api_client.get(url, {"search": "Alpha"})
        assert len(response.json()) == 1


@pytest.mark.django_db
class TestResumoProgramaSistema:

    # TC-PR02 — Cenário: Retornar resumo de programa existente (status 200)
    def test_retorna_200_para_programa_existente(self, api_client, programa):
        url = reverse("resumo_programa", args=[programa.id])
        response = api_client.get(url)
        assert response.status_code == 200

    # TC-PR02 — Cenário: Programa inexistente (404 + body {'error': 'Programa não encontrado'})
    def test_retorna_404_para_programa_inexistente(self, api_client):
        url = reverse("resumo_programa", args=[99999])
        response = api_client.get(url)
        assert response.status_code == 404
        assert response.json() == {"error": "Programa não encontrado"}

    # Complementar ao TC-PR02: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse("resumo_programa", args=[programa.id])
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-PR02 — Contrato: total_projetos, horas_estimadas, horas_realizadas, custo_estimado e custo_real
    def test_retorna_estrutura_correta(self, api_client, programa):
        url = reverse("resumo_programa", args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert "total_projetos" in data
        assert "horas_estimadas" in data
        assert "horas_realizadas" in data
        assert "custo_estimado" in data
        assert "custo_real" in data


@pytest.mark.django_db
class TestDistribuicaoStatusSistema:

    # TC-PR03 — Status 200 no endpoint de distribuição de status
    def test_retorna_200_para_programa_existente(self, api_client, programa):
        url = reverse("distribuicao_status", args=[programa.id])
        response = api_client.get(url)
        assert response.status_code == 200

    # Complementar ao TC-PR03: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse("distribuicao_status", args=[programa.id])
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-PR03 — Contrato: body com total e status
    def test_retorna_estrutura_correta(self, api_client, programa):
        url = reverse("distribuicao_status", args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert "total" in data
        assert "status" in data

    # TC-PR03 — Cenário: Programa sem projetos (total=0 e status=[])
    def test_retorna_vazio_sem_projetos(self, api_client, programa):
        url = reverse("distribuicao_status", args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data["total"] == 0
        assert data["status"] == []

    # TC-PR03 — Cenário: Retornar distribuição com múltiplos status
    def test_retorna_dados_corretos_com_projetos(self, api_client, programa):
        baker.make("api.DimProjeto", id=10, programa=programa, status="Planejamento")
        baker.make("api.DimProjeto", id=11, programa=programa, status="Planejamento")
        baker.make("api.DimProjeto", id=12, programa=programa, status="Planejamento")
        baker.make("api.DimProjeto", id=13, programa=programa, status="Concluído")
        baker.make("api.DimProjeto", id=14, programa=programa, status="Concluído")
        url = reverse("distribuicao_status", args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data["total"] == 5
        assert len(data["status"]) == 2


@pytest.mark.django_db
class TestBurnupHorasProgramasSistema:

    # TC-PR04 — Status 200 no endpoint GET /api/programas-burnup-horas/
    def test_retorna_200_para_get(self, api_client):
        url = reverse("programas_burnup_horas")
        response = api_client.get(url)
        assert response.status_code == 200

    # Complementar ao TC-PR04: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client):
        url = reverse("programas_burnup_horas")
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-PR04 — Cenário: Nenhum registro de horas (body [])
    def test_retorna_lista_vazia_sem_dados(self, api_client):
        url = reverse("programas_burnup_horas")
        response = api_client.get(url)
        assert response.json() == []

    # TC-PR04 — Contrato: resposta é uma lista JSON
    def test_resposta_e_lista_json(self, api_client):
        url = reverse("programas_burnup_horas")
        response = api_client.get(url)
        assert isinstance(response.json(), list)

    # TC-PR04 — Cenário/Contrato: série temporal com date_str e values{codigo_programa, nome_programa, horas}
    def test_estrutura_dos_grupos_e_valores(self, api_client):
        from datetime import date

        programa = baker.make(
            "api.DimPrograma", codigo_programa="PROG-1", nome_programa="Alpha"
        )
        projeto = baker.make("api.DimProjeto", id=1, programa=programa)
        tempo = baker.make(
            "api.DimTempo",
            id=20250110,
            data=date(2025, 1, 10),
            ano=2025,
            mes=1,
            trimestre=1,
            semestre=1,
            dia_semana=date(2025, 1, 10).weekday(),
        )
        baker.make(
            "api.FatoHoras",
            programa=programa,
            projeto=projeto,
            tempo=tempo,
            horas_trabalhadas=4.0,
            custo_horas=0,
        )
        url = reverse("programas_burnup_horas")
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1
        grupo = data[0]
        assert "date_str" in grupo
        assert "values" in grupo
        ponto = grupo["values"][0]
        assert "codigo_programa" in ponto
        assert "nome_programa" in ponto
        assert "horas" in ponto
        assert Decimal(str(ponto["horas"])) == Decimal("4.0")


@pytest.mark.django_db
class TestBurnupCustoProgramasSistema:

    # TC-PR05 — Status 200 no endpoint GET /api/programas-burnup-custo/
    def test_retorna_200_para_get(self, api_client):
        url = reverse("programas_burnup_custo")
        response = api_client.get(url)
        assert response.status_code == 200

    # Complementar ao TC-PR05: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client):
        url = reverse("programas_burnup_custo")
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-PR05 — Cenário: Nenhum registro de custo (body [])
    def test_retorna_lista_vazia_sem_dados(self, api_client):
        url = reverse("programas_burnup_custo")
        response = api_client.get(url)
        assert response.json() == []

    # TC-PR05 — Contrato: resposta é uma lista JSON
    def test_resposta_e_lista_json(self, api_client):
        url = reverse("programas_burnup_custo")
        response = api_client.get(url)
        assert isinstance(response.json(), list)

    # TC-PR05 — Cenário/Contrato: série temporal com date_str e values{codigo_programa, nome_programa, custo}
    def test_estrutura_dos_grupos_e_valores(self, api_client):
        from datetime import date

        programa = baker.make(
            "api.DimPrograma", codigo_programa="PROG-1", nome_programa="Alpha"
        )
        projeto = baker.make("api.DimProjeto", id=1, programa=programa)
        tempo = baker.make(
            "api.DimTempo",
            id=20250110,
            data=date(2025, 1, 10),
            ano=2025,
            mes=1,
            trimestre=1,
            semestre=1,
            dia_semana=date(2025, 1, 10).weekday(),
        )
        baker.make(
            "api.FatoHoras",
            programa=programa,
            projeto=projeto,
            tempo=tempo,
            horas_trabalhadas=0,
            custo_horas=400.0,
        )
        url = reverse("programas_burnup_custo")
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1
        grupo = data[0]
        assert "date_str" in grupo
        assert "values" in grupo
        ponto = grupo["values"][0]
        assert "codigo_programa" in ponto
        assert "nome_programa" in ponto
        assert "custo" in ponto


@pytest.mark.django_db
class TestTabelaProjetosSistema:

    # TC-PR06 — Status 200 no endpoint de tabela de projetos
    def test_retorna_200_para_programa_existente(self, api_client, programa):
        url = reverse("tabela_projetos", args=[programa.id])
        response = api_client.get(url)
        assert response.status_code == 200

    # TC-PR06 — Cenário: Programa inexistente (404 + body {'error': 'Programa não encontrado'})
    def test_retorna_404_para_programa_inexistente(self, api_client):
        url = reverse("tabela_projetos", args=[99999])
        response = api_client.get(url)
        assert response.status_code == 404
        assert response.json() == {"error": "Programa não encontrado"}

    # Complementar ao TC-PR06: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse("tabela_projetos", args=[programa.id])
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-PR06 — Cenário: sort_by inválido (usa nome_projeto como padrão)
    def test_sort_by_invalido_usa_ordenacao_padrao(self, api_client, programa):
        baker.make("api.DimProjeto", id=50, programa=programa, nome_projeto="Zebra")
        baker.make("api.DimProjeto", id=51, programa=programa, nome_projeto="Alpha")
        url = reverse("tabela_projetos", args=[programa.id])
        response = api_client.get(url, {"sort_by": "campo_inexistente"})
        assert response.status_code == 200
        nomes = [r["nome_projeto"] for r in response.json()["results"]]
        assert nomes == sorted(nomes)  # padrão: nome_projeto asc

    # TC-PR06 — Cenário: sort_dir inválido (usa asc como padrão)
    def test_sort_dir_invalido_usa_asc_como_padrao(self, api_client, programa):
        baker.make("api.DimProjeto", id=52, programa=programa, nome_projeto="Zebra")
        baker.make("api.DimProjeto", id=53, programa=programa, nome_projeto="Alpha")
        url = reverse("tabela_projetos", args=[programa.id])
        response = api_client.get(url, {"sort_dir": "random"})
        assert response.status_code == 200
        nomes = [r["nome_projeto"] for r in response.json()["results"]]
        assert nomes == sorted(nomes)  # padrão: asc

    # Complementar ao TC-PR06: programa sem projetos retorna contrato paginado vazio
    def test_retorna_lista_vazia_sem_projetos(self, api_client, programa):
        url = reverse("tabela_projetos", args=[programa.id])
        response = api_client.get(url)
        assert response.json() == {
            "count": 0,
            "page": 1,
            "page_size": 10,
            "total_pages": 1,
            "results": [],
        }

    # TC-PR06 — Contrato paginado e campos dos itens de results
    def test_retorna_estrutura_correta(self, api_client, programa):
        baker.make("api.DimProjeto", id=10, programa=programa)
        url = reverse("tabela_projetos", args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data["count"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total_pages"] == 1
        item = data["results"][0]
        assert "nome_projeto" in item
        assert "responsavel" in item
        assert "status" in item
        assert "horas_estimadas" in item
        assert "horas_realizadas" in item
        assert "percentual_tarefas_concluidas" in item
        assert "desvio_horas" in item
        assert "percentual_desvio" in item

    # TC-PR06 — Cenário: Retornar primeira página (um item por projeto)
    def test_retorna_um_item_por_projeto(self, api_client, programa):
        baker.make("api.DimProjeto", id=10, programa=programa)
        baker.make("api.DimProjeto", id=11, programa=programa)
        baker.make("api.DimProjeto", id=12, programa=programa)
        url = reverse("tabela_projetos", args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data["count"] == 3
        assert len(data["results"]) == 3

    # TC-PR06 — Contrato: total_tarefas, tarefas_concluidas e percentuais
    def test_retorna_dados_corretos_com_tarefas_concluidas(self, api_client, programa):
        projeto = baker.make("api.DimProjeto", id=10, programa=programa)
        baker.make(
            "api.DimTarefa",
            id=1,
            projeto=projeto,
            horas_estimadas=10.0,
            status="Concluída",
        )
        baker.make(
            "api.DimTarefa",
            id=2,
            projeto=projeto,
            horas_estimadas=10.0,
            status="Em andamento",
        )
        url = reverse("tabela_projetos", args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data["results"][0]["percentual_tarefas_concluidas"] == pytest.approx(
            50.0
        )

    # Complementar ao TC-PR06: parâmetro page é respeitado
    def test_retorna_pagina_solicitada(self, api_client, programa):
        baker.make("api.DimProjeto", programa=programa, _quantity=12)
        url = reverse("tabela_projetos", args=[programa.id])
        response = api_client.get(url, {"page": 2})
        data = response.json()
        assert data["count"] == 12
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert data["total_pages"] == 2
        assert len(data["results"]) == 2


@pytest.mark.django_db
class TestProgramaErrosSistema:

    # Fora da especificação: erro interno (500) no resumo do programa
    def test_resumo_retorna_500_quando_service_levanta_excecao(
        self, api_client, programa
    ):
        url = reverse("resumo_programa", args=[programa.id])
        with patch(
            "api.views.programa_view.get_resumo_programa",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500

    # Fora da especificação: erro interno (500) na distribuição de status
    def test_distribuicao_status_retorna_500_quando_service_levanta_excecao(
        self, api_client, programa
    ):
        url = reverse("distribuicao_status", args=[programa.id])
        with patch(
            "api.views.programa_view.get_distribuicao_status",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500

    # Fora da especificação: erro interno (500) no burnup de horas
    def test_burnup_horas_retorna_500_quando_service_levanta_excecao(self, api_client):
        url = reverse("programas_burnup_horas")
        with patch(
            "api.views.programa_view.get_burnup_horas_programas",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500

    # Fora da especificação: erro interno (500) no burnup de custo
    def test_burnup_custo_retorna_500_quando_service_levanta_excecao(self, api_client):
        url = reverse("programas_burnup_custo")
        with patch(
            "api.views.programa_view.get_burnup_custo_programas",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500

    # Complementar ao TC-PR06: page inválida retorna 400
    def test_tabela_projetos_retorna_400_para_pagina_invalida(
        self, api_client, programa
    ):
        url = reverse("tabela_projetos", args=[programa.id])
        response = api_client.get(url, {"page": "abc"})
        assert response.status_code == 400

    # Fora da especificação: erro interno (500) na tabela de projetos
    def test_tabela_projetos_retorna_500_quando_service_levanta_excecao(
        self, api_client, programa
    ):
        url = reverse("tabela_projetos", args=[programa.id])
        with patch(
            "api.views.programa_view.get_tabela_projetos",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500


@pytest.mark.django_db
class TestHorasPorProjetoSistema:

    # TC-PR07 — Status 200 no endpoint de horas por projeto
    def test_retorna_200_para_programa_existente(self, api_client, programa):
        url = reverse("horas_por_projeto", args=[programa.id])
        response = api_client.get(url)
        assert response.status_code == 200

    # TC-PR07 — Cenário: Programa inexistente (404 + body {'error': 'Programa não encontrado'})
    def test_retorna_404_para_programa_inexistente(self, api_client):
        url = reverse("horas_por_projeto", args=[99999])
        response = api_client.get(url)
        assert response.status_code == 404
        assert response.json() == {"error": "Programa não encontrado"}

    # Complementar ao TC-PR07: método POST não permitido (405)
    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse("horas_por_projeto", args=[programa.id])
        response = api_client.post(url)
        assert response.status_code == 405

    # TC-PR07 — Cenário: Programa sem projetos com horas (body [])
    def test_retorna_lista_vazia_sem_projetos(self, api_client, programa):
        url = reverse("horas_por_projeto", args=[programa.id])
        response = api_client.get(url)
        assert response.json() == []

    # TC-PR07 — Contrato: resposta é uma lista JSON
    def test_retorna_lista_json(self, api_client, programa):
        url = reverse("horas_por_projeto", args=[programa.id])
        response = api_client.get(url)
        assert isinstance(response.json(), list)

    # TC-PR07 — Contrato: cada item possui nome_projeto e horas_realizadas
    def test_retorna_estrutura_correta_com_projetos(self, api_client, programa):
        baker.make("api.DimProjeto", id=20, programa=programa, nome_projeto="Projeto X")
        url = reverse("horas_por_projeto", args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1
        assert "nome_projeto" in data[0]
        assert "horas_realizadas" in data[0]

    # TC-PR07 — Cenário: Retornar horas por projeto (soma das horas)
    def test_horas_realizadas_soma_fato_horas(self, api_client, programa):
        from datetime import date as d

        projeto = baker.make(
            "api.DimProjeto", id=21, programa=programa, nome_projeto="Projeto Y"
        )
        tempo = baker.make(
            "api.DimTempo",
            id=20230301,
            data=d(2023, 3, 1),
            ano=2023,
            mes=3,
            trimestre=1,
            semestre=1,
            dia_semana=d(2023, 3, 1).weekday(),
        )
        baker.make(
            "api.FatoHoras",
            projeto=projeto,
            programa=programa,
            tempo=tempo,
            horas_trabalhadas=6.0,
            custo_horas=0,
        )
        baker.make(
            "api.FatoHoras",
            projeto=projeto,
            programa=programa,
            tempo=tempo,
            horas_trabalhadas=4.0,
            custo_horas=0,
        )
        url = reverse("horas_por_projeto", args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data[0]["horas_realizadas"] == pytest.approx(10.0)

    # Complementar ao TC-PR07: projeto sem horas exibe 0
    def test_projeto_sem_horas_exibe_zero(self, api_client, programa):
        baker.make("api.DimProjeto", id=22, programa=programa, nome_projeto="Projeto Z")
        url = reverse("horas_por_projeto", args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data[0]["horas_realizadas"] == pytest.approx(0.0)

    # Fora da especificação: erro interno (500)
    def test_retorna_500_quando_service_levanta_excecao(self, api_client, programa):
        url = reverse("horas_por_projeto", args=[programa.id])
        with patch(
            "api.views.programa_view.get_horas_por_projeto",
            side_effect=RuntimeError("falha"),
        ):
            response = api_client.get(url)
        assert response.status_code == 500
