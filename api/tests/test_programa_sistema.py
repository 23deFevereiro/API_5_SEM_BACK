import pytest
from model_bakery import baker
from django.test import RequestFactory
from api.views.programa_view import listar_programas_view, get_resumo_programa_view, get_distribuicao_status_view


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


@pytest.mark.django_db
class TestGetDistribuicaoStatusView:

    def test_retorna_200_para_programa_existente(self):
        programa = baker.make('api.Programa')
        factory = RequestFactory()
        request = factory.get(f'/programas/{programa.id}/distribuicao-status/')
        response = get_distribuicao_status_view(request, programa.id)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        programa = baker.make('api.Programa')
        factory = RequestFactory()
        request = factory.post(f'/programas/{programa.id}/distribuicao-status/')
        response = get_distribuicao_status_view(request, programa.id)
        assert response.status_code == 405

    def test_retorna_estrutura_correta(self):
        import json
        programa = baker.make('api.Programa')
        factory = RequestFactory()
        request = factory.get(f'/programas/{programa.id}/distribuicao-status/')
        response = get_distribuicao_status_view(request, programa.id)
        data = json.loads(response.content)
        assert 'total' in data
        assert 'status' in data

    def test_retorna_lista_vazia_quando_sem_projetos(self):
        import json
        programa = baker.make('api.Programa')
        factory = RequestFactory()
        request = factory.get(f'/programas/{programa.id}/distribuicao-status/')
        response = get_distribuicao_status_view(request, programa.id)
        data = json.loads(response.content)
        assert data['total'] == 0
        assert data['status'] == []

    def test_retorna_dados_corretos_para_programa_com_projetos(self):
        import json
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa, status='Planejamento', _quantity=3)
        baker.make('api.Projeto', programa=programa, status='Concluído', _quantity=2)
        factory = RequestFactory()
        request = factory.get(f'/programas/{programa.id}/distribuicao-status/')
        response = get_distribuicao_status_view(request, programa.id)
        data = json.loads(response.content)
        assert data['total'] == 5
        assert len(data['status']) == 2

    def test_retorna_500_quando_exception(self):
        from unittest.mock import patch
        factory = RequestFactory()
        request = factory.get('/programas/1/distribuicao-status/')
        with patch('api.views.programa_view.get_distribuicao_status', side_effect=Exception('erro simulado')):
            response = get_distribuicao_status_view(request, 1)
        assert response.status_code == 500