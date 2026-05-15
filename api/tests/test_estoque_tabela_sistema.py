import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
class TestGetEstoqueTabelaView:

    def test_retorna_200_get(self, client):
        resp = client.get("/api/compras/estoque-tabela/")
        assert resp.status_code == 200

    def test_retorna_json_com_chaves_de_paginacao(self, client):
        resp = client.get("/api/compras/estoque-tabela/")
        data = resp.json()
        assert "count" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "results" in data

    def test_results_e_lista(self, client):
        resp = client.get("/api/compras/estoque-tabela/")
        assert isinstance(resp.json()["results"], list)

    def test_retorna_vazio_sem_dados(self, client):
        resp = client.get("/api/compras/estoque-tabela/")
        data = resp.json()
        assert data["count"] == 0
        assert data["results"] == []

    def test_nao_aceita_post(self, client):
        resp = client.post("/api/compras/estoque-tabela/")
        assert resp.status_code == 405

    def test_content_type_json(self, client):
        resp = client.get("/api/compras/estoque-tabela/")
        assert "application/json" in resp["Content-Type"]

    def test_aceita_parametros_critico_max_e_atencao_max(self, client):
        resp = client.get("/api/compras/estoque-tabela/?critico_max=90&atencao_max=180")
        assert resp.status_code == 200

    def test_aceita_parametro_page(self, client):
        resp = client.get("/api/compras/estoque-tabela/?page=2")
        assert resp.status_code == 200

    def test_parametros_invalidos_retornam_400(self, client):
        resp = client.get("/api/compras/estoque-tabela/?critico_max=abc")
        assert resp.status_code == 400

    def test_page_invalida_retorna_400(self, client):
        resp = client.get("/api/compras/estoque-tabela/?page=xyz")
        assert resp.status_code == 400

    def test_atencao_max_ajustado_quando_menor_que_critico_max(self, client):
        resp = client.get("/api/compras/estoque-tabela/?critico_max=30&atencao_max=10")
        assert resp.status_code == 200

    def test_aceita_material_id(self, client):
        resp = client.get("/api/compras/estoque-tabela/?material_id=1")
        assert resp.status_code == 200

    def test_material_id_invalido_retorna_400(self, client):
        resp = client.get("/api/compras/estoque-tabela/?material_id=abc")
        assert resp.status_code == 400
