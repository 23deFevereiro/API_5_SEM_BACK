from unittest.mock import patch

import pytest
from django.test import Client

from api.services.horas_svc import get_burnup_horas_projetos


@patch("api.services.horas_svc.FatoHoras")
# TC-P07 — Cenário: Retornar série temporal de burnup (unitário, serviço mockado)
def test_burnup_basico(mock_fato_horas):
    queryset_mock = mock_fato_horas.objects.filter.return_value.values.return_value

    order_by_mock = queryset_mock.annotate.return_value.order_by

    order_by_mock.return_value = [
        {
            "projeto__id": 1,
            "projeto__codigo_projeto": "PROJ-A",
            "tempo__ano": 2026,
            "tempo__mes": 4,
            "total_horas": 2,
        },
        {
            "projeto__id": 1,
            "projeto__codigo_projeto": "PROJ-A",
            "tempo__ano": 2026,
            "tempo__mes": 5,
            "total_horas": 3,
        },
    ]

    resultado = get_burnup_horas_projetos()

    resultado = get_burnup_horas_projetos()
    serie = resultado[0]["serie"]

    assert len(resultado) == 1
    assert resultado[0]["projeto"] == "PROJ-A"
    assert serie[0]["mes"] == "04/2026"
    assert serie[0]["horas"] == pytest.approx(2.0)
    assert serie[0]["horas_acumuladas"] == pytest.approx(2.0)
    assert serie[1]["mes"] == "05/2026"
    assert serie[1]["horas"] == pytest.approx(3.0)
    assert serie[1]["horas_acumuladas"] == pytest.approx(5.0)


@patch("api.services.horas_svc.FatoHoras")
# TC-P07 — Cenário: horas_acumuladas crescentes mês a mês (unitário, serviço mockado)
def test_burnup_acumula_horas_por_mes(mock_fato_horas):
    queryset_mock = mock_fato_horas.objects.filter.return_value.values.return_value

    order_by_mock = queryset_mock.annotate.return_value.order_by

    order_by_mock.return_value = [
        {
            "projeto__id": 1,
            "projeto__codigo_projeto": "PROJ-A",
            "tempo__ano": 2026,
            "tempo__mes": 4,
            "total_horas": 1,
        },
        {
            "projeto__id": 1,
            "projeto__codigo_projeto": "PROJ-A",
            "tempo__ano": 2026,
            "tempo__mes": 5,
            "total_horas": 5,
        },
    ]

    resultado = get_burnup_horas_projetos()

    serie = resultado[0]["serie"]

    assert serie[-1]["mes"] == "05/2026"
    assert serie[-1]["horas"] == pytest.approx(5.0)
    assert serie[-1]["horas_acumuladas"] == pytest.approx(6.0)


@patch("api.services.horas_svc.FatoHoras")
# TC-P07 — Cenário: Nenhum apontamento no banco (unitário, serviço mockado)
def test_burnup_vazio(mock_fato_horas):
    queryset_mock = mock_fato_horas.objects.filter.return_value.values.return_value

    annotate_mock = queryset_mock.annotate.return_value.order_by

    annotate_mock.return_value = []

    resultado = get_burnup_horas_projetos()

    assert resultado == []


@patch("api.services.horas_svc.FatoHoras")
# TC-P07 — Cenário: série separada por projeto (unitário, serviço mockado)
def test_burnup_multiplos_projetos(mock_fato_horas):
    queryset_mock = mock_fato_horas.objects.filter.return_value.values.return_value

    order_by_mock = queryset_mock.annotate.return_value.order_by

    order_by_mock.return_value = [
        {
            "projeto__id": 1,
            "projeto__codigo_projeto": "PROJ-A",
            "tempo__ano": 2026,
            "tempo__mes": 4,
            "total_horas": 2,
        },
        {
            "projeto__id": 2,
            "projeto__codigo_projeto": "PROJ-B",
            "tempo__ano": 2026,
            "tempo__mes": 4,
            "total_horas": 4,
        },
    ]

    resultado = get_burnup_horas_projetos()

    assert len(resultado) == 2
    nomes = [item["projeto"] for item in resultado]
    assert "PROJ-A" in nomes
    assert "PROJ-B" in nomes


@pytest.mark.django_db
@patch("api.views.horas_view.get_burnup_horas_projetos")
# TC-P07 — Status 200 no endpoint GET /api/projetos/burnup-horas/ (view com serviço mockado)
def test_view_burnup_status_200(mock_service):
    mock_service.return_value = [
        {
            "projeto_id": 1,
            "projeto": "Projeto A",
            "serie": [
                {
                    "mes": "04/2026",
                    "horas": 5.0,
                    "horas_acumuladas": 5.0,
                }
            ],
        }
    ]

    client = Client()
    response = client.get("/api/projetos/burnup-horas/")

    assert response.status_code == 200


@pytest.mark.django_db
@patch("api.views.horas_view.get_burnup_horas_projetos")
# TC-P07 — Contrato: projeto_id, projeto e serie{mes, horas, horas_acumuladas} (view com serviço mockado)
def test_view_burnup_retorna_json(mock_service):
    mock_service.return_value = [
        {
            "projeto_id": 1,
            "projeto": "Projeto A",
            "serie": [
                {
                    "mes": "04/2026",
                    "horas": 5.0,
                    "horas_acumuladas": 5.0,
                }
            ],
        }
    ]

    client = Client()
    response = client.get("/api/projetos/burnup-horas/")

    assert response.status_code == 200
    assert response.json() == [
        {
            "projeto_id": 1,
            "projeto": "Projeto A",
            "serie": [
                {
                    "mes": "04/2026",
                    "horas": 5.0,
                    "horas_acumuladas": 5.0,
                }
            ],
        }
    ]


@patch("api.services.horas_svc.FatoHoras")
# TC-P07 — Cenário: Filtrar por programa_id (unitário, serviço mockado)
def test_burnup_com_programa_id(mock_fato_horas):
    queryset_mock = mock_fato_horas.objects.filter.return_value.values.return_value

    order_by_mock = queryset_mock.annotate.return_value.order_by

    order_by_mock.return_value = [
        {
            "projeto__id": 1,
            "projeto__codigo_projeto": "PROJ-A",
            "tempo__ano": 2026,
            "tempo__mes": 4,
            "total_horas": 3,
        }
    ]

    resultado = get_burnup_horas_projetos(programa_id=1)

    assert len(resultado) == 1
    mock_fato_horas.objects.filter.assert_called_once_with(
        projeto__status__in=["Em andamento", "Concluído"],
        projeto__programa_id=1,
    )


@patch("api.services.horas_svc.FatoHoras")
# Complementar ao TC-P07: filtro de status dos projetos no queryset
def test_burnup_sem_programa_id_verifica_filtro_status(mock_fato_horas):
    queryset_mock = mock_fato_horas.objects.filter.return_value.values.return_value

    annotate_mock = queryset_mock.annotate.return_value.order_by

    annotate_mock.return_value = []

    get_burnup_horas_projetos()

    mock_fato_horas.objects.filter.assert_called_once_with(
        projeto__status__in=["Em andamento", "Concluído"],
    )


# ---------------------------------------------------------------------------
# Testes de integração (banco real) — complementam os testes unitários acima
# que usam serviço mockado, validando os cenários do TC-P07 ponta a ponta.
# ---------------------------------------------------------------------------


def _make_tempo_burnup(ano, mes, dia=1):
    from datetime import date as _date

    from model_bakery import baker as _baker

    from api.models import DimTempo

    _id = ano * 10000 + mes * 100 + dia
    existente = DimTempo.objects.filter(id=_id).first()
    if existente:
        return existente
    return _baker.make(
        "api.DimTempo",
        id=_id,
        data=_date(ano, mes, dia),
        ano=ano,
        mes=mes,
        trimestre=(mes - 1) // 3 + 1,
        semestre=1 if mes <= 6 else 2,
        dia_semana=_date(ano, mes, dia).weekday(),
    )


@pytest.mark.django_db
class TestBurnupHorasProjetosIntegracao:

    def _make_fato(self, projeto, programa, ano, mes, horas):
        from model_bakery import baker as _baker

        tempo = _make_tempo_burnup(ano, mes)
        return _baker.make(
            "api.FatoHoras",
            projeto=projeto,
            programa=programa,
            tempo=tempo,
            horas_trabalhadas=horas,
            custo_horas=0,
        )

    # TC-P07 — Cenário: Retornar série temporal de burnup (integração com banco; fev >= jan)
    def test_serie_temporal_com_horas_acumuladas_crescentes(self):
        from model_bakery import baker as _baker

        programa = _baker.make("api.DimPrograma")
        projeto = _baker.make(
            "api.DimProjeto", programa=programa, status="Em andamento"
        )
        self._make_fato(projeto, programa, 2026, 1, horas=5.0)
        self._make_fato(projeto, programa, 2026, 2, horas=3.0)

        client = Client()
        response = client.get("/api/projetos/burnup-horas/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        item = data[0]
        assert "projeto_id" in item
        assert "projeto" in item
        serie = item["serie"]
        assert {"mes", "horas", "horas_acumuladas"} <= set(serie[0].keys())
        jan, fev = serie[0], serie[1]
        assert jan["mes"] == "01/2026"
        assert fev["mes"] == "02/2026"
        assert fev["horas_acumuladas"] >= jan["horas_acumuladas"]
        assert fev["horas_acumuladas"] == pytest.approx(8.0)

    # TC-P07 — Cenário: Filtrar por programa_id (integração com banco)
    def test_filtra_por_programa_id(self):
        from model_bakery import baker as _baker

        programa_a = _baker.make("api.DimPrograma")
        programa_b = _baker.make("api.DimPrograma")
        projeto_a = _baker.make(
            "api.DimProjeto",
            programa=programa_a,
            status="Em andamento",
            codigo_projeto="PRJ-A",
        )
        projeto_b = _baker.make(
            "api.DimProjeto",
            programa=programa_b,
            status="Em andamento",
            codigo_projeto="PRJ-B",
        )
        self._make_fato(projeto_a, programa_a, 2026, 1, horas=4.0)
        self._make_fato(projeto_b, programa_b, 2026, 1, horas=6.0)

        client = Client()
        response = client.get(
            f"/api/projetos/burnup-horas/?programa_id={programa_a.id}"
        )

        assert response.status_code == 200
        data = response.json()
        ids = [item["projeto_id"] for item in data]
        assert projeto_a.id in ids
        assert projeto_b.id not in ids

    # TC-P07 — Cenário: Nenhum apontamento no banco (integração; body [])
    def test_sem_apontamentos_retorna_lista_vazia(self):
        client = Client()
        response = client.get("/api/projetos/burnup-horas/")
        assert response.status_code == 200
        assert response.json() == []
