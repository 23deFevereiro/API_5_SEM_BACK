from decimal import Decimal
from unittest.mock import patch

import pytest
from model_bakery import baker
from django.urls import reverse


@pytest.fixture
def programa():
    return baker.make('api.DimPrograma', id=1)


@pytest.mark.django_db
class TestListarProgramasSistema:

    def test_retorna_200_para_get(self, api_client, programa):
        url = reverse('listar_programas')
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse('listar_programas')
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_programas(self, api_client):
        url = reverse('listar_programas')
        response = api_client.get(url)
        assert response.json() == []

    def test_filtra_por_search(self, api_client):
        baker.make('api.DimPrograma', nome_programa='Programa Alpha')
        baker.make('api.DimPrograma', nome_programa='Programa Beta')
        url = reverse('listar_programas')
        response = api_client.get(url, {'search': 'Alpha'})
        assert len(response.json()) == 1


@pytest.mark.django_db
class TestResumoProgramaSistema:

    def test_retorna_200_para_programa_existente(self, api_client, programa):
        url = reverse('resumo_programa', args=[programa.id])
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_404_para_programa_inexistente(self, api_client):
        url = reverse('resumo_programa', args=[99999])
        response = api_client.get(url)
        assert response.status_code == 404

    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse('resumo_programa', args=[programa.id])
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_estrutura_correta(self, api_client, programa):
        url = reverse('resumo_programa', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert 'total_projetos' in data
        assert 'horas_estimadas' in data
        assert 'horas_realizadas' in data
        assert 'custo_estimado' in data
        assert 'custo_real' in data


@pytest.mark.django_db
class TestDistribuicaoStatusSistema:

    def test_retorna_200_para_programa_existente(self, api_client, programa):
        url = reverse('distribuicao_status', args=[programa.id])
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse('distribuicao_status', args=[programa.id])
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_estrutura_correta(self, api_client, programa):
        url = reverse('distribuicao_status', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert 'total' in data
        assert 'status' in data

    def test_retorna_vazio_sem_projetos(self, api_client, programa):
        url = reverse('distribuicao_status', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data['total'] == 0
        assert data['status'] == []

    def test_retorna_dados_corretos_com_projetos(self, api_client, programa):
        baker.make('api.DimProjeto', id=10, programa=programa, status='Planejamento')
        baker.make('api.DimProjeto', id=11, programa=programa, status='Planejamento')
        baker.make('api.DimProjeto', id=12, programa=programa, status='Planejamento')
        baker.make('api.DimProjeto', id=13, programa=programa, status='Concluído')
        baker.make('api.DimProjeto', id=14, programa=programa, status='Concluído')
        url = reverse('distribuicao_status', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data['total'] == 5
        assert len(data['status']) == 2

@pytest.mark.django_db
class TestBurnupHorasProgramasSistema:

    def test_retorna_200_para_get(self, api_client):
        url = reverse('programas_burnup_horas')
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client):
        url = reverse('programas_burnup_horas')
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_dados(self, api_client):
        url = reverse('programas_burnup_horas')
        response = api_client.get(url)
        assert response.json() == []

    def test_resposta_e_lista_json(self, api_client):
        url = reverse('programas_burnup_horas')
        response = api_client.get(url)
        assert isinstance(response.json(), list)

    def test_estrutura_dos_grupos_e_valores(self, api_client):
        from datetime import date
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = baker.make(
            'api.DimTempo',
            id=20250110,
            data=date(2025, 1, 10),
            ano=2025,
            mes=1,
            trimestre=1,
            semestre=1,
            dia_semana=date(2025, 1, 10).weekday(),
        )
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo, horas_trabalhadas=4.0, custo_horas=0)
        url = reverse('programas_burnup_horas')
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1
        grupo = data[0]
        assert 'date_str' in grupo
        assert 'values' in grupo
        ponto = grupo['values'][0]
        assert 'codigo_programa' in ponto
        assert 'nome_programa' in ponto
        assert 'horas' in ponto
        assert Decimal(str(ponto['horas'])) == Decimal('4.0')


@pytest.mark.django_db
class TestBurnupCustoProgramasSistema:

    def test_retorna_200_para_get(self, api_client):
        url = reverse('programas_burnup_custo')
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_405_para_post(self, api_client):
        url = reverse('programas_burnup_custo')
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_dados(self, api_client):
        url = reverse('programas_burnup_custo')
        response = api_client.get(url)
        assert response.json() == []

    def test_resposta_e_lista_json(self, api_client):
        url = reverse('programas_burnup_custo')
        response = api_client.get(url)
        assert isinstance(response.json(), list)

    def test_estrutura_dos_grupos_e_valores(self, api_client):
        from datetime import date
        programa = baker.make('api.DimPrograma', codigo_programa='PROG-1', nome_programa='Alpha')
        projeto = baker.make('api.DimProjeto', id=1, programa=programa)
        tempo = baker.make(
            'api.DimTempo',
            id=20250110,
            data=date(2025, 1, 10),
            ano=2025,
            mes=1,
            trimestre=1,
            semestre=1,
            dia_semana=date(2025, 1, 10).weekday(),
        )
        baker.make('api.FatoHoras', programa=programa, projeto=projeto,
                   tempo=tempo, horas_trabalhadas=0, custo_horas=400.0)
        url = reverse('programas_burnup_custo')
        response = api_client.get(url)
        data = response.json()
        assert len(data) == 1
        grupo = data[0]
        assert 'date_str' in grupo
        assert 'values' in grupo
        ponto = grupo['values'][0]
        assert 'codigo_programa' in ponto
        assert 'nome_programa' in ponto
        assert 'custo' in ponto


@pytest.mark.django_db
class TestTabelaProjetosSistema:

    def test_retorna_200_para_programa_existente(self, api_client, programa):
        url = reverse('tabela_projetos', args=[programa.id])
        response = api_client.get(url)
        assert response.status_code == 200

    def test_retorna_404_para_programa_inexistente(self, api_client):
        url = reverse('tabela_projetos', args=[99999])
        response = api_client.get(url)
        assert response.status_code == 404

    def test_retorna_405_para_post(self, api_client, programa):
        url = reverse('tabela_projetos', args=[programa.id])
        response = api_client.post(url)
        assert response.status_code == 405

    def test_retorna_lista_vazia_sem_projetos(self, api_client, programa):
        url = reverse('tabela_projetos', args=[programa.id])
        response = api_client.get(url)
        assert response.json() == {
            'count': 0,
            'page': 1,
            'page_size': 10,
            'total_pages': 1,
            'results': [],
        }

    def test_retorna_estrutura_correta(self, api_client, programa):
        baker.make('api.DimProjeto', id=10, programa=programa)
        url = reverse('tabela_projetos', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data['count'] == 1
        assert data['page'] == 1
        assert data['page_size'] == 10
        assert data['total_pages'] == 1
        item = data['results'][0]
        assert 'nome_projeto' in item
        assert 'responsavel' in item
        assert 'status' in item
        assert 'horas_estimadas' in item
        assert 'horas_realizadas' in item
        assert 'percentual_tarefas_concluidas' in item
        assert 'desvio_horas' in item
        assert 'percentual_desvio' in item

    def test_retorna_um_item_por_projeto(self, api_client, programa):
        baker.make('api.DimProjeto', id=10, programa=programa)
        baker.make('api.DimProjeto', id=11, programa=programa)
        baker.make('api.DimProjeto', id=12, programa=programa)
        url = reverse('tabela_projetos', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data['count'] == 3
        assert len(data['results']) == 3

    def test_retorna_dados_corretos_com_tarefas_concluidas(self, api_client, programa):
        projeto = baker.make('api.DimProjeto', id=10, programa=programa)
        baker.make('api.DimTarefa', id=1, projeto=projeto, horas_estimadas=10.0, status='Concluída')
        baker.make('api.DimTarefa', id=2, projeto=projeto, horas_estimadas=10.0, status='Em andamento')
        url = reverse('tabela_projetos', args=[programa.id])
        response = api_client.get(url)
        data = response.json()
        assert data['results'][0]['percentual_tarefas_concluidas'] == pytest.approx(50.0)

    def test_retorna_pagina_solicitada(self, api_client, programa):
        baker.make('api.DimProjeto', programa=programa, _quantity=12)
        url = reverse('tabela_projetos', args=[programa.id])
        response = api_client.get(url, {'page': 2})
        data = response.json()
        assert data['count'] == 12
        assert data['page'] == 2
        assert data['page_size'] == 10
        assert data['total_pages'] == 2
        assert len(data['results']) == 2


@pytest.mark.django_db
class TestProgramaErrosSistema:

    def test_resumo_retorna_500_quando_service_levanta_excecao(self, api_client, programa):
        url = reverse('resumo_programa', args=[programa.id])
        with patch('api.views.programa_view.get_resumo_programa', side_effect=RuntimeError('falha')):
            response = api_client.get(url)
        assert response.status_code == 500

    def test_distribuicao_status_retorna_500_quando_service_levanta_excecao(self, api_client, programa):
        url = reverse('distribuicao_status', args=[programa.id])
        with patch('api.views.programa_view.get_distribuicao_status', side_effect=RuntimeError('falha')):
            response = api_client.get(url)
        assert response.status_code == 500

    def test_burnup_horas_retorna_500_quando_service_levanta_excecao(self, api_client):
        url = reverse('programas_burnup_horas')
        with patch('api.views.programa_view.get_burnup_horas_programas', side_effect=RuntimeError('falha')):
            response = api_client.get(url)
        assert response.status_code == 500

    def test_burnup_custo_retorna_500_quando_service_levanta_excecao(self, api_client):
        url = reverse('programas_burnup_custo')
        with patch('api.views.programa_view.get_burnup_custo_programas', side_effect=RuntimeError('falha')):
            response = api_client.get(url)
        assert response.status_code == 500

    def test_tabela_projetos_retorna_400_para_pagina_invalida(self, api_client, programa):
        url = reverse('tabela_projetos', args=[programa.id])
        response = api_client.get(url, {'page': 'abc'})
        assert response.status_code == 400

    def test_tabela_projetos_retorna_500_quando_service_levanta_excecao(self, api_client, programa):
        url = reverse('tabela_projetos', args=[programa.id])
        with patch('api.views.programa_view.get_tabela_projetos', side_effect=RuntimeError('falha')):
            response = api_client.get(url)
        assert response.status_code == 500
