# Fora da especificação de testes de integração: valida a documentação
# Swagger/OpenAPI da API.
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestSwaggerSistema:

    def test_retorna_swagger_ui(self, api_client):
        response = api_client.get(reverse("schema-swagger-ui"))

        assert response.status_code == 200

    def test_retorna_schema_json(self, api_client):
        response = api_client.get(reverse("schema-json", kwargs={"format": "json"}))

        assert response.status_code == 200
        assert response.json()["info"]["title"] == "FATEC API 5 Semestre"
