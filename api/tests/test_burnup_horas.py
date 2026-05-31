from unittest.mock import patch

import pytest
from django.test import Client

from api.services.horas_svc import get_burnup_horas_projetos


@patch("api.services.horas_svc.FatoHoras")
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
def test_burnup_vazio(mock_fato_horas):
    queryset_mock = mock_fato_horas.objects.filter.return_value.values.return_value

    annotate_mock = queryset_mock.annotate.return_value.order_by

    annotate_mock.return_value = []

    resultado = get_burnup_horas_projetos()

    assert resultado == []


@patch("api.services.horas_svc.FatoHoras")
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
def test_burnup_sem_programa_id_verifica_filtro_status(mock_fato_horas):
    queryset_mock = mock_fato_horas.objects.filter.return_value.values.return_value

    annotate_mock = queryset_mock.annotate.return_value.order_by

    annotate_mock.return_value = []

    get_burnup_horas_projetos()

    mock_fato_horas.objects.filter.assert_called_once_with(
        projeto__status__in=["Em andamento", "Concluído"],
    )
