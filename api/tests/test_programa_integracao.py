import pytest
from model_bakery import baker
from django.test import RequestFactory
from api.views.programa_view import listar_programas_view
from api.services.programa_svc import listar_programas


@pytest.mark.django_db
class TestListarProgramas:

    def test_retorna_lista_vazia_quando_nao_ha_programas(self):
        resultado = listar_programas()
        assert resultado == []

    def test_retorna_programas_quando_existem(self):
        baker.make('api.Programa', _quantity=3)
        resultado = listar_programas()
        assert len(resultado) == 3

    def test_filtra_por_nome_quando_search_informado(self):
        baker.make('api.Programa', nome_programa='Programa Alpha')
        baker.make('api.Programa', nome_programa='Programa Beta')
        resultado = listar_programas(search='Alpha')
        assert len(resultado) == 1
        assert resultado[0]['nome'] == 'Programa Alpha'

    def test_retorna_campos_id_e_nome(self):
        baker.make('api.Programa', nome_programa='Aeroespacial')
        resultado = listar_programas()
        assert 'id' in resultado[0]
        assert 'nome' in resultado[0]
        assert resultado[0]['nome'] == 'Aeroespacial'


@pytest.mark.django_db
class TestListarProgramasView:

    def test_retorna_200_para_get(self):
        factory = RequestFactory()
        request = factory.get('/programas')
        response = listar_programas_view(request)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/programas')
        response = listar_programas_view(request)
        assert response.status_code == 405

    def test_retorna_json_com_programas(self):
        baker.make('api.Programa', nome_programa='Defesa')
        factory = RequestFactory()
        request = factory.get('/programas')
        response = listar_programas_view(request)

        import json
        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]['nome'] == 'Defesa'
