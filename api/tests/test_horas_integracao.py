import pytest
from pytest import approx
from model_bakery import baker
from django.test import RequestFactory
from api.views.horas_view import get_horas_por_funcionario_view
from api.services.horas_svc import get_horas_por_funcionario


@pytest.mark.django_db
class TestGetHorasPorFuncionario:

    def test_retorna_lista_vazia_quando_projeto_sem_tarefas(self):
        projeto = baker.make('api.Projeto')
        resultado = get_horas_por_funcionario(projeto.id)
        assert resultado == []

    def test_retorna_lista_vazia_quando_tarefas_sem_registros_de_tempo(self):
        projeto = baker.make('api.Projeto')
        baker.make('api.Tarefa', projeto=projeto)
        resultado = get_horas_por_funcionario(projeto.id)
        assert resultado == []

    def test_retorna_horas_de_um_funcionario(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Ana', horas_trabalhadas=6.0)
        resultado = get_horas_por_funcionario(projeto.id)
        assert len(resultado) == 1
        assert resultado[0]['funcionario'] == 'Ana'
        assert resultado[0]['total_horas'] == approx(6.0)

    def test_agrega_multiplos_registros_do_mesmo_funcionario(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Carlos', horas_trabalhadas=4.0)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Carlos', horas_trabalhadas=3.5)
        resultado = get_horas_por_funcionario(projeto.id)
        assert len(resultado) == 1
        assert resultado[0]['total_horas'] == approx(7.5)

    def test_agrega_registros_entre_multiplas_tarefas(self):
        projeto = baker.make('api.Projeto')
        tarefa1 = baker.make('api.Tarefa', projeto=projeto)
        tarefa2 = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa1, usuario='Maria', horas_trabalhadas=5.0)
        baker.make('api.TempoTarefa', tarefa=tarefa2, usuario='Maria', horas_trabalhadas=3.0)
        resultado = get_horas_por_funcionario(projeto.id)
        assert len(resultado) == 1
        assert resultado[0]['total_horas'] == approx(8.0)

    def test_retorna_multiplos_funcionarios(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Ana', horas_trabalhadas=4.0)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Bruno', horas_trabalhadas=6.0)
        resultado = get_horas_por_funcionario(projeto.id)
        assert len(resultado) == 2
        usuarios = [r['funcionario'] for r in resultado]
        assert 'Ana' in usuarios
        assert 'Bruno' in usuarios

    def test_nao_inclui_horas_de_outro_projeto(self):
        projeto1 = baker.make('api.Projeto')
        projeto2 = baker.make('api.Projeto')
        tarefa1 = baker.make('api.Tarefa', projeto=projeto1)
        tarefa2 = baker.make('api.Tarefa', projeto=projeto2)
        baker.make('api.TempoTarefa', tarefa=tarefa1, usuario='Ana', horas_trabalhadas=8.0)
        baker.make('api.TempoTarefa', tarefa=tarefa2, usuario='Carlos', horas_trabalhadas=5.0)
        resultado = get_horas_por_funcionario(projeto1.id)
        assert len(resultado) == 1
        assert resultado[0]['funcionario'] == 'Ana'

    def test_retorna_campos_corretos(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='João', horas_trabalhadas=2.0)
        resultado = get_horas_por_funcionario(projeto.id)
        assert 'funcionario' in resultado[0]
        assert 'total_horas' in resultado[0]

    def test_total_horas_e_float(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Lia', horas_trabalhadas=2.5)
        resultado = get_horas_por_funcionario(projeto.id)
        assert isinstance(resultado[0]['total_horas'], float)


@pytest.mark.django_db
class TestGetHorasPorFuncionarioView:

    def test_retorna_200_para_projeto_existente(self):
        projeto = baker.make('api.Projeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/horas-por-funcionario/')
        response = get_horas_por_funcionario_view(request, projeto.id)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/projetos/1/horas-por-funcionario/')
        response = get_horas_por_funcionario_view(request, 1)
        assert response.status_code == 405

    def test_retorna_lista_json(self):
        import json
        projeto = baker.make('api.Projeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/horas-por-funcionario/')
        response = get_horas_por_funcionario_view(request, projeto.id)
        data = json.loads(response.content)
        assert isinstance(data, list)

    def test_retorna_dados_corretos_na_resposta(self):
        import json
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, usuario='Pedro', horas_trabalhadas=10.0)
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/horas-por-funcionario/')
        response = get_horas_por_funcionario_view(request, projeto.id)
        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]['funcionario'] == 'Pedro'
        assert data[0]['total_horas'] == approx(10.0)