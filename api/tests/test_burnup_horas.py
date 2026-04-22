from datetime import date
from unittest.mock import patch

import pytest
from django.test import Client

from api.services.horas_svc import get_burnup_horas_projetos


@patch("api.services.horas_svc.TempoTarefa")
def test_burnup_basico(mock_tempo):
    mock_tempo.objects.select_related.return_value.values.return_value.annotate.return_value.order_by.return_value = [
        {
            "tarefa__projeto__id": 1,
            "tarefa__projeto__nome_projeto": "Projeto A",
            "data": date(2026, 4, 1),
            "total_horas": 2,
        },
        {
            "tarefa__projeto__id": 1,
            "tarefa__projeto__nome_projeto": "Projeto A",
            "data": date(2026, 4, 2),
            "total_horas": 3,
        },
    ]

    resultado = get_burnup_horas_projetos()

    assert len(resultado) == 1
    assert resultado[0]["projeto"] == "Projeto A"
    assert resultado[0]["serie"][0]["semana"] == "Semana 1"
    assert resultado[0]["serie"][0]["horas"] == pytest.approx(5.0)
    assert resultado[0]["serie"][0]["horas_acumuladas"] == pytest.approx(5.0)


@patch("api.services.horas_svc.TempoTarefa")
def test_burnup_semana_4_mais(mock_tempo):
    mock_tempo.objects.select_related.return_value.values.return_value.annotate.return_value.order_by.return_value = [
        {
            "tarefa__projeto__id": 1,
            "tarefa__projeto__nome_projeto": "Projeto A",
            "data": date(2026, 4, 1),
            "total_horas": 1,
        },
        {
            "tarefa__projeto__id": 1,
            "tarefa__projeto__nome_projeto": "Projeto A",
            "data": date(2026, 5, 10),
            "total_horas": 5,
        },
    ]

    resultado = get_burnup_horas_projetos()

    assert resultado[0]["serie"][-1]["semana"] == "Semana 4+"
    assert resultado[0]["serie"][-1]["horas"] == pytest.approx(5.0)
    assert resultado[0]["serie"][-1]["horas_acumuladas"] == pytest.approx(6.0)


@patch("api.services.horas_svc.TempoTarefa")
def test_burnup_vazio(mock_tempo):
    mock_tempo.objects.select_related.return_value.values.return_value.annotate.return_value.order_by.return_value = []

    resultado = get_burnup_horas_projetos()

    assert resultado == []


@patch("api.services.horas_svc.TempoTarefa")
def test_burnup_multiplos_projetos(mock_tempo):
    mock_tempo.objects.select_related.return_value.values.return_value.annotate.return_value.order_by.return_value = [
        {
            "tarefa__projeto__id": 1,
            "tarefa__projeto__nome_projeto": "Projeto A",
            "data": date(2026, 4, 1),
            "total_horas": 2,
        },
        {
            "tarefa__projeto__id": 2,
            "tarefa__projeto__nome_projeto": "Projeto B",
            "data": date(2026, 4, 1),
            "total_horas": 4,
        },
    ]

    resultado = get_burnup_horas_projetos()

    assert len(resultado) == 2
    nomes = [item["projeto"] for item in resultado]
    assert "Projeto A" in nomes
    assert "Projeto B" in nomes


@pytest.mark.django_db
@patch("api.views.horas_view.get_burnup_horas_projetos")
def test_view_burnup_status_200(mock_service):
    mock_service.return_value = [
        {
            "projeto_id": 1,
            "projeto": "Projeto A",
            "serie": [
                {
                    "semana": "Semana 1",
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
                    "semana": "Semana 1",
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
                    "semana": "Semana 1",
                    "horas": 5.0,
                    "horas_acumuladas": 5.0,
                }
            ],
        }
    ]