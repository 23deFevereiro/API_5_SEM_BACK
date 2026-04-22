import json
import pytest
from datetime import date
from model_bakery import baker
from django.test import RequestFactory
from api.views.funcionario_view import get_funcionarios_projeto_view
from api.services.funcionario_svc import get_funcionarios_projeto


@pytest.mark.django_db
class TestGetFuncionariosProjeto:

    def test_retorna_lista_vazia_quando_projeto_sem_tarefas(self):
        projeto = baker.make('api.Projeto')
        resultado = get_funcionarios_projeto(projeto.id)
        assert resultado['results'] == []
        assert resultado['count'] == 0

    def test_retorna_funcionario_com_horas_do_projeto(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Alberto', horas_trabalhadas=8.0)
        resultado = get_funcionarios_projeto(projeto.id)
        assert resultado['count'] == 1
        assert resultado['results'][0]['usuario'] == 'Alberto'

    def test_soma_horas_do_mesmo_usuario(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Breno', horas_trabalhadas=4.0)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Breno', horas_trabalhadas=6.0)
        resultado = get_funcionarios_projeto(projeto.id)
        assert resultado['count'] == 1
        assert resultado['results'][0]['total_horas'] == pytest.approx(10.0)

    def test_retorna_multiplos_funcionarios(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Alberto', horas_trabalhadas=8.0)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Breno', horas_trabalhadas=4.0)
        resultado = get_funcionarios_projeto(projeto.id)
        assert resultado['count'] == 2

    def test_nao_retorna_funcionarios_de_outro_projeto(self):
        projeto1 = baker.make('api.Projeto')
        projeto2 = baker.make('api.Projeto')
        tarefa2 = baker.make('api.Tarefa', projeto=projeto2)
        baker.make('api.TempoTarefa', tarefa=tarefa2, usuario='Cruzoé', horas_trabalhadas=6.0)
        resultado = get_funcionarios_projeto(projeto1.id)
        assert resultado['count'] == 0

    def test_retorna_projetos_que_funcionario_participa(self):
        projeto1 = baker.make('api.Projeto', codigo_projeto='P001')
        projeto2 = baker.make('api.Projeto', codigo_projeto='P002')
        tarefa1 = baker.make('api.Tarefa', projeto=projeto1)
        tarefa2 = baker.make('api.Tarefa', projeto=projeto2)
        baker.make('api.TempoTarefa', tarefa=tarefa1, usuario='Alberto', horas_trabalhadas=8.0)
        baker.make('api.TempoTarefa', tarefa=tarefa2, usuario='Alberto', horas_trabalhadas=4.0)
        resultado = get_funcionarios_projeto(projeto1.id)
        assert 'P001' in resultado['results'][0]['projetos']
        assert 'P002' in resultado['results'][0]['projetos']

    def test_paginacao_retorna_page_size_correto(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        for i in range(15):
            baker.make('api.TempoTarefa', tarefa=tarefa, usuario=f'Usuario {i:02d}', horas_trabalhadas=1.0)
        resultado = get_funcionarios_projeto(projeto.id, page=1, page_size=10)
        assert len(resultado['results']) == 10
        assert resultado['total_pages'] == 2

    def test_paginacao_segunda_pagina(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        for i in range(15):
            baker.make('api.TempoTarefa', tarefa=tarefa, usuario=f'Usuario {i:02d}', horas_trabalhadas=1.0)
        resultado = get_funcionarios_projeto(projeto.id, page=2, page_size=10)
        assert len(resultado['results']) == 5

    def test_retorna_estrutura_de_paginacao_correta(self):
        projeto = baker.make('api.Projeto')
        resultado = get_funcionarios_projeto(projeto.id)
        assert 'count' in resultado
        assert 'page' in resultado
        assert 'page_size' in resultado
        assert 'total_pages' in resultado
        assert 'results' in resultado

    def test_total_pages_e_um_quando_sem_resultados(self):
        projeto = baker.make('api.Projeto')
        resultado = get_funcionarios_projeto(projeto.id)
        assert resultado['total_pages'] == 1

    def test_total_horas_retornado_como_float(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Dalia', horas_trabalhadas=5.0)
        resultado = get_funcionarios_projeto(projeto.id)
        assert isinstance(resultado['results'][0]['total_horas'], float)

    def test_projetos_retornados_como_lista(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Estevao', horas_trabalhadas=3.0)
        resultado = get_funcionarios_projeto(projeto.id)
        assert isinstance(resultado['results'][0]['projetos'], list)

    def test_page_minima_e_um(self):
        projeto = baker.make('api.Projeto')
        resultado = get_funcionarios_projeto(projeto.id, page=0)
        assert resultado['page'] == 1

    def test_filtra_por_periodo(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Ana',
                   data=date(2025, 1, 10), horas_trabalhadas=4.0)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Bruno',
                   data=date(2025, 6, 10), horas_trabalhadas=3.0)
        resultado = get_funcionarios_projeto(projeto.id,
                                             data_inicio='2025-06-01',
                                             data_fim='2025-06-30')
        usuarios = [r['usuario'] for r in resultado['results']]
        assert 'Bruno' in usuarios
        assert 'Ana' not in usuarios

    def test_filtra_por_nome_funcionario(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Ana', horas_trabalhadas=4.0)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Bruno', horas_trabalhadas=3.0)
        resultado = get_funcionarios_projeto(projeto.id, funcionario='Ana')
        usuarios = [r['usuario'] for r in resultado['results']]
        assert usuarios == ['Ana']


@pytest.mark.django_db
class TestGetFuncionariosProjetoView:

    def test_retorna_200_para_projeto_existente(self):
        projeto = baker.make('api.Projeto')
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
        projeto = baker.make('api.Projeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/funcionarios/')
        response = get_funcionarios_projeto_view(request, projeto.id)
        data = json.loads(response.content)
        assert 'count' in data
        assert 'page' in data
        assert 'total_pages' in data
        assert 'results' in data

    def test_retorna_funcionarios_do_projeto(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Alberto', horas_trabalhadas=8.0)
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/funcionarios/')
        response = get_funcionarios_projeto_view(request, projeto.id)
        data = json.loads(response.content)
        assert data['count'] == 1
        assert data['results'][0]['usuario'] == 'Alberto'

    def test_aceita_parametro_de_pagina(self):
        projeto = baker.make('api.Projeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/funcionarios/', {'page': 2})
        response = get_funcionarios_projeto_view(request, projeto.id)
        data = json.loads(response.content)
        assert data['page'] == 2