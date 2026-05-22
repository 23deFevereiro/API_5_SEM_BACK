from django.urls import reverse
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

    def test_aceita_parametros_critico_max_e_atencao_max(self, client):
        resp = client.get('/api/compras/alertas/?critico_max=90&atencao_max=180')
        assert resp.status_code == 200
        data = resp.json()
        assert 'criticos' in data
        assert 'atencao' in data

    def test_parametros_invalidos_retornam_400(self, client):
        resp = client.get('/api/compras/alertas/?critico_max=abc')
        assert resp.status_code == 400

    def test_atencao_max_ajustado_quando_menor_que_critico_max(self, client):
        resp = client.get('/api/compras/alertas/?critico_max=30&atencao_max=10')
        assert resp.status_code == 200

@pytest.mark.django_db
class TestSugestaoProximaCompraSistema:

    def test_retorna_200_para_get(self, api_client):
        url = reverse('compras_sugestao_proxima_compra')
        response = api_client.get(url)

        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client):
        url = reverse('compras_sugestao_proxima_compra')
        response = api_client.post(url)

        assert response.status_code == 405

    def test_data_referencia_invalida_retorna_400(self, api_client):
        url = reverse('compras_sugestao_proxima_compra')
        response = api_client.get(url, {'data_referencia': '01-04-2024'})

        assert response.status_code == 400
        assert response.json() == {
            'error': 'data_referencia deve estar no formato YYYY-MM-DD'
        }