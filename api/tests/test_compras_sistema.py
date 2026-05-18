import pytest
from model_bakery import baker
from django.urls import reverse


@pytest.fixture
def material_com_compra():
    material = baker.make('api.DimMaterial', codigo_material='M001', descricao='Capacitor')
    fornecedor = baker.make('api.DimFornecedor', razao_social='Fornecedor Alpha')
    status = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
    tempo = baker.make('api.DimTempo', id=20240101, data='2024-01-01',
                       ano=2024, mes=1, trimestre=1, semestre=1, dia_semana=0)
    baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
               tempo=tempo, status=status, lead_time=10,
               valor_total=500.0, quantidade_solicitada=5)
    return material


@pytest.mark.django_db
class TestListarMateriaisComprasSistema:

    def test_retorna_200_para_get(self, api_client):
        url = reverse('compras_materiais')
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client):
        url = reverse('compras_materiais')
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_dados(self, api_client):
        url = reverse('compras_materiais')
        response = api_client.get(url)
        assert response.json() == []

    def test_retorna_material_existente(self, api_client, material_com_compra):
        url = reverse('compras_materiais')
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1
        assert data[0]['codigo_material'] == 'M001'
        assert data[0]['descricao'] == 'Capacitor'

    def test_retorna_json(self, api_client):
        url = reverse('compras_materiais')
        response = api_client.get(url)
        assert response['Content-Type'] == 'application/json'


@pytest.mark.django_db
class TestLeadTimeSistema:

    def test_retorna_400_sem_material_id(self, api_client):
        url = reverse('compras_lead_time')
        response = api_client.get(url)
        assert response.status_code == 400

    def test_retorna_400_para_material_id_invalido(self, api_client):
        url = reverse('compras_lead_time')
        response = api_client.get(url, {'material_id': 'abc'})
        assert response.status_code == 400

    def test_retorna_405_para_post(self, api_client):
        url = reverse('compras_lead_time')
        response = api_client.post(url, {'material_id': 1})
        assert response.status_code == 405

    def test_retorna_lista_vazia_para_material_sem_compras(self, api_client):
        material = baker.make('api.DimMaterial')
        url = reverse('compras_lead_time')
        response = api_client.get(url, {'material_id': material.id})
        assert response.status_code == 200
        assert response.json() == []

    def test_retorna_lista_vazia_para_material_inexistente(self, api_client):
        url = reverse('compras_lead_time')
        response = api_client.get(url, {'material_id': 99999})
        assert response.status_code == 200
        assert response.json() == []

    def test_retorna_pontos_corretos(self, api_client, material_com_compra):
        url = reverse('compras_lead_time')
        response = api_client.get(url, {'material_id': material_com_compra.id})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        ponto = data[0]
        assert ponto['fornecedor'] == 'Fornecedor Alpha'
        assert ponto['lead_time'] == 10
        assert ponto['status'] == 'Entregue'
        assert ponto['categoria_status'] == 'Concluído'
        assert ponto['data_pedido'] == '2024-01-01'
        assert 'valor_unidade' in ponto
        assert 'valor_total' in ponto

    def test_retorna_json(self, api_client, material_com_compra):
        url = reverse('compras_lead_time')
        response = api_client.get(url, {'material_id': material_com_compra.id})
        assert response['Content-Type'] == 'application/json'