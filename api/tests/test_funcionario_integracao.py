import json
import pytest
from datetime import date
from model_bakery import baker
from django.test import RequestFactory
from api.views.funcionario_view import get_funcionarios_projeto_view
from api.services.funcionario_svc import get_funcionarios_projeto


def make_fato_horas(projeto, funcionario, horas, tempo=None, programa=None, tarefa=None):
    if programa is None:
        programa = baker.make('api.DimPrograma')
    if tempo is None:
        tempo = baker.make('api.DimTempo')
    if tarefa is None:
        tarefa = baker.make('api.DimTarefa', projeto=projeto)
    return baker.make('api.FatoHoras', projeto=projeto, programa=programa,
                      funcionario=funcionario, tarefa=tarefa, tempo=tempo,
                      horas_trabalhadas=horas, custo_horas=0)


@pytest.mark.django_db
class TestGetFuncionariosProjeto:

    def test_retorna_lista_vazia_quando_projeto_sem_dados(self):
        projeto = baker.make('api.DimProjeto')
        resultado = get_funcionarios_projeto(projeto.id)
        assert resultado['results'] == []
        assert resultado['count'] == 0

    def test_retorna_funcionario_com_horas_do_projeto(self):
        projeto = baker.make('api.DimProjeto')
        funcionario = baker.make('api.DimFuncionario', nome='Alberto')
        make_fato_horas(projeto, funcionario, horas=8.0)
        resultado = get_funcionarios_projeto(projeto.id)
        assert resultado['count'] == 1
        assert resultado['results'][0]['funcionario'] == 'Alberto'

    def test_soma_horas_do_mesmo_usuario(self):
        projeto = baker.make('api.DimProjeto')
        funcionario = baker.make('api.DimFuncionario', nome='Breno')
        tempo = baker.make('api.DimTempo', data=date(2025, 1, 1))
        make_fato_horas(projeto, funcionario, horas=4.0, tempo=tempo)
        make_fato_horas(projeto, funcionario, horas=6.0, tempo=tempo)
        resultado = get_funcionarios_projeto(projeto.id)
        assert resultado['count'] == 1
        assert resultado['results'][0]['total_horas'] == pytest.approx(10.0)

    def test_retorna_multiplos_funcionarios(self):
        projeto = baker.make('api.DimProjeto')
        alberto = baker.make('api.DimFuncionario', nome='Alberto')
        breno = baker.make('api.DimFuncionario', nome='Breno')
        tempo = baker.make('api.DimTempo', data=date(2025, 1, 1))
        make_fato_horas(projeto, alberto, horas=8.0, tempo=tempo)
        make_fato_horas(projeto, breno, horas=4.0, tempo=tempo)
        resultado = get_funcionarios_projeto(projeto.id)
        assert resultado['count'] == 2

    def test_nao_retorna_funcionarios_de_outro_projeto(self):
        projeto1 = baker.make('api.DimProjeto')
        projeto2 = baker.make('api.DimProjeto')
        cruzoe = baker.make('api.DimFuncionario', nome='Cruzoé')
        make_fato_horas(projeto2, cruzoe, horas=6.0)
        resultado = get_funcionarios_projeto(projeto1.id)
        assert resultado['count'] == 0

    def test_retorna_projetos_que_funcionario_participa(self):
        projeto1 = baker.make('api.DimProjeto', codigo_projeto='P001')
        projeto2 = baker.make('api.DimProjeto', codigo_projeto='P002')
        alberto = baker.make('api.DimFuncionario', nome='Alberto')
        tempo = baker.make('api.DimTempo', data=date(2025, 1, 1))
        make_fato_horas(projeto1, alberto, horas=8.0, tempo=tempo)
        make_fato_horas(projeto2, alberto, horas=4.0, tempo=tempo)
        resultado = get_funcionarios_projeto(projeto1.id)
        assert 'P001' in resultado['results'][0]['projetos']
        assert 'P002' in resultado['results'][0]['projetos']

    def test_paginacao_retorna_page_size_correto(self):
        projeto = baker.make('api.DimProjeto')
        tempo = baker.make('api.DimTempo', data=date(2025, 1, 1))
        for i in range(15):
            f = baker.make('api.DimFuncionario', nome=f'Usuario {i:02d}')
            make_fato_horas(projeto, f, horas=1.0, tempo=tempo)
        resultado = get_funcionarios_projeto(projeto.id, page=1, page_size=10)
        assert len(resultado['results']) == 10
        assert resultado['total_pages'] == 2

    def test_paginacao_segunda_pagina(self):
        projeto = baker.make('api.DimProjeto')
        tempo = baker.make('api.DimTempo', data=date(2025, 1, 1))
        for i in range(15):
            f = baker.make('api.DimFuncionario', nome=f'Usuario {i:02d}')
            make_fato_horas(projeto, f, horas=1.0, tempo=tempo)
        resultado = get_funcionarios_projeto(projeto.id, page=2, page_size=10)
        assert len(resultado['results']) == 5

    def test_retorna_estrutura_de_paginacao_correta(self):
        projeto = baker.make('api.DimProjeto')
        resultado = get_funcionarios_projeto(projeto.id)
        assert 'count' in resultado
        assert 'page' in resultado
        assert 'page_size' in resultado
        assert 'total_pages' in resultado
        assert 'results' in resultado

    def test_total_pages_e_um_quando_sem_resultados(self):
        projeto = baker.make('api.DimProjeto')
        resultado = get_funcionarios_projeto(projeto.id)
        assert resultado['total_pages'] == 1

    def test_total_horas_retornado_como_float(self):
        projeto = baker.make('api.DimProjeto')
        funcionario = baker.make('api.DimFuncionario', nome='Dalia')
        make_fato_horas(projeto, funcionario, horas=5.0)
        resultado = get_funcionarios_projeto(projeto.id)
        assert isinstance(resultado['results'][0]['total_horas'], float)

    def test_projetos_retornados_como_lista(self):
        projeto = baker.make('api.DimProjeto')
        funcionario = baker.make('api.DimFuncionario', nome='Estevao')
        make_fato_horas(projeto, funcionario, horas=3.0)
        resultado = get_funcionarios_projeto(projeto.id)
        assert isinstance(resultado['results'][0]['projetos'], list)

    def test_page_minima_e_um(self):
        projeto = baker.make('api.DimProjeto')
        resultado = get_funcionarios_projeto(projeto.id, page=0)
        assert resultado['page'] == 1

    def test_filtra_por_periodo(self):
        projeto = baker.make('api.DimProjeto')
        ana = baker.make('api.DimFuncionario', nome='Ana')
        bruno = baker.make('api.DimFuncionario', nome='Bruno')
        tempo1 = baker.make('api.DimTempo', data=date(2025, 1, 10))
        tempo2 = baker.make('api.DimTempo', data=date(2025, 6, 10))
        make_fato_horas(projeto, ana, horas=4.0, tempo=tempo1)
        make_fato_horas(projeto, bruno, horas=3.0, tempo=tempo2)
        resultado = get_funcionarios_projeto(projeto.id,
                                             data_inicio='2025-06-01',
                                             data_fim='2025-06-30')
        usuarios = [r['funcionario'] for r in resultado['results']]
        assert 'Bruno' in usuarios
        assert 'Ana' not in usuarios

    def test_filtra_por_nome_funcionario(self):
        projeto = baker.make('api.DimProjeto')
        ana = baker.make('api.DimFuncionario', nome='Ana')
        bruno = baker.make('api.DimFuncionario', nome='Bruno')
        tempo = baker.make('api.DimTempo', data=date(2025, 1, 1))
        make_fato_horas(projeto, ana, horas=4.0, tempo=tempo)
        make_fato_horas(projeto, bruno, horas=3.0, tempo=tempo)
        resultado = get_funcionarios_projeto(projeto.id, funcionario='Ana')
        usuarios = [r['funcionario'] for r in resultado['results']]
        assert usuarios == ['Ana']


@pytest.mark.django_db
class TestGetFuncionariosProjetoView:

    def test_retorna_200_para_projeto_existente(self):
        projeto = baker.make('api.DimProjeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/funcionarios/')
        response = get_funcionarios_projeto_view(request, projeto.id)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/projetos/1/funcionarios/')
        response = get_funcionarios_projeto_view(request, 1)
        assert response.status_code == 405

    def test_retorna_estrutura_correta(self):
        projeto = baker.make('api.DimProjeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/funcionarios/')
        response = get_funcionarios_projeto_view(request, projeto.id)
        data = json.loads(response.content)
        assert 'count' in data
        assert 'page' in data
        assert 'total_pages' in data
        assert 'results' in data

    def test_retorna_funcionarios_do_projeto(self):
        projeto = baker.make('api.DimProjeto')
        funcionario = baker.make('api.DimFuncionario', nome='Alberto')
        make_fato_horas(projeto, funcionario, horas=8.0)
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/funcionarios/')
        response = get_funcionarios_projeto_view(request, projeto.id)
        data = json.loads(response.content)
        assert data['count'] == 1
        assert data['results'][0]['funcionario'] == 'Alberto'

    def test_aceita_parametro_de_pagina(self):
        projeto = baker.make('api.DimProjeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/funcionarios/', {'page': 2})
        response = get_funcionarios_projeto_view(request, projeto.id)
        data = json.loads(response.content)
        assert data['page'] == 2