import pytest
from model_bakery import baker
from django.test import RequestFactory
from api.views.programa_view import listar_programas_view, get_resumo_programa_view


@pytest.mark.django_db
class TestListarProgramasView:

    def test_retorna_200_para_get(self):
        factory = RequestFactory()
        request = factory.get('/programas/')
        response = listar_programas_view(request)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/programas/')
        response = listar_programas_view(request)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_programas(self):
        import json
        factory = RequestFactory()
        request = factory.get('/programas/')
        response = listar_programas_view(request)
        data = json.loads(response.content)
        assert data == []

    def test_filtra_por_search(self):
        import json
        baker.make('api.Programa', nome_programa='Programa Alpha')
        baker.make('api.Programa', nome_programa='Programa Beta')
        factory = RequestFactory()
        request = factory.get('/programas/?search=Alpha')
        response = listar_programas_view(request)
        data = json.loads(response.content)
        assert len(data) == 1


@pytest.mark.django_db
class TestGetResumoProgramaView:

    def test_retorna_200_para_programa_existente(self):
        programa = baker.make('api.Programa')
        factory = RequestFactory()
        request = factory.get(f'/programas/{programa.id}/resumo/')
        response = get_resumo_programa_view(request, programa.id)
        assert response.status_code == 200

    def test_retorna_404_para_programa_inexistente(self):
        factory = RequestFactory()
        request = factory.get('/programas/99999/resumo/')
        response = get_resumo_programa_view(request, 99999)
        assert response.status_code == 404

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/programas/1/resumo/')
        response = get_resumo_programa_view(request, 1)
        assert response.status_code == 405

    def test_retorna_estrutura_correta(self):
        import json
        programa = baker.make('api.Programa')
        factory = RequestFactory()
        request = factory.get(f'/programas/{programa.id}/resumo/')
        response = get_resumo_programa_view(request, programa.id)
        data = json.loads(response.content)
        assert 'total_projetos' in data
        assert 'horas_estimadas' in data
        assert 'horas_realizadas' in data
        assert 'custo_estimado' in data
        assert 'custo_real' in data
