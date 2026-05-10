import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
class TestGetAlertasView:

    def test_retorna_200_get(self, client):
        resp = client.get('/api/compras/alertas/')
        assert resp.status_code == 200

    def test_retorna_json_com_chaves_criticos_e_atencao(self, client):
        resp = client.get('/api/compras/alertas/')
        data = resp.json()
        assert 'criticos' in data
        assert 'atencao' in data

    def test_chaves_sao_listas(self, client):
        resp = client.get('/api/compras/alertas/')
        data = resp.json()
        assert isinstance(data['criticos'], list)
        assert isinstance(data['atencao'], list)

    def test_retorna_listas_vazias_sem_dados(self, client):
        resp = client.get('/api/compras/alertas/')
        data = resp.json()
        assert data == {'criticos': [], 'atencao': []}

    def test_content_type_json(self, client):
        resp = client.get('/api/compras/alertas/')
        assert 'application/json' in resp['Content-Type']

    def test_nao_aceita_post(self, client):
        resp = client.post('/api/compras/alertas/')
        assert resp.status_code == 405
