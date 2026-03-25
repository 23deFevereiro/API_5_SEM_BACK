import pytest
from model_bakery import baker
from django.test import RequestFactory
from api.views.projeto_view import listar_projetos_view, get_resumo_projeto_view
from api.services.projeto_svc import listar_projetos, get_resumo_projeto


@pytest.mark.django_db
class TestListarProjetos:

    def test_retorna_lista_vazia_quando_nao_ha_projetos(self):
        resultado = listar_projetos()
        assert resultado == []

    def test_retorna_projetos_quando_existem(self):
        baker.make('api.Projeto', nome_projeto='Conversor DC-DC', _quantity=3)
        resultado = listar_projetos()
        assert len(resultado) == 3

    def test_filtra_por_nome_quando_search_informado(self):
        baker.make('api.Projeto', nome_projeto='Conversor DC-DC')
        baker.make('api.Projeto', nome_projeto='Driver LED')
        resultado = listar_projetos(search='Conversor')
        assert len(resultado) == 1
        assert resultado[0]['nome_projeto'] == 'Conversor DC-DC'

    def test_retorna_campos_corretos(self):
        baker.make('api.Projeto', nome_projeto='Teste')
        resultado = listar_projetos()
        assert 'id' in resultado[0]
        assert 'codigo_projeto' in resultado[0]
        assert 'nome_projeto' in resultado[0]


@pytest.mark.django_db
class TestGetResumoProjeto:

    def test_retorna_zeros_quando_projeto_sem_dados(self):
        projeto = baker.make('api.Projeto')
        resultado = get_resumo_projeto(projeto.id)
        assert resultado['custo_materiais'] == 0.0
        assert resultado['custo_compras'] == 0.0
        assert resultado['tempo_total'] == 0.0

    def test_calcula_custo_materiais_corretamente(self):
        projeto = baker.make('api.Projeto')
        material = baker.make('api.Material', custo_estimado=100.00)
        baker.make('api.EstoqueMaterialProjeto', projeto=projeto, material=material, quantidade=5)
        resultado = get_resumo_projeto(projeto.id)
        assert resultado['custo_materiais'] == 500.0

    def test_exclui_compras_canceladas_do_calculo(self):
        projeto = baker.make('api.Projeto')
        pedido_cancelado = baker.make('api.PedidoCompra', status='Cancelado')
        pedido_ativo = baker.make('api.PedidoCompra', status='Entregue')
        baker.make('api.ComprasProjeto', projeto=projeto, pedido_compra=pedido_cancelado, valor_alocado=1000.00)
        baker.make('api.ComprasProjeto', projeto=projeto, pedido_compra=pedido_ativo, valor_alocado=500.00)
        resultado = get_resumo_projeto(projeto.id)
        assert resultado['custo_compras'] == 500.0

    def test_calcula_tempo_total_das_tarefas(self):
        projeto = baker.make('api.Projeto')
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, horas_trabalhadas=8.0)
        baker.make('api.TempoTarefa', tarefa=tarefa, horas_trabalhadas=4.5)
        resultado = get_resumo_projeto(projeto.id)
        assert resultado['tempo_total'] == 12.5


@pytest.mark.django_db
class TestListarProjetosView:

    def test_retorna_200_para_get(self):
        factory = RequestFactory()
        request = factory.get('/projetos/')
        response = listar_projetos_view(request)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/projetos/')
        response = listar_projetos_view(request)
        assert response.status_code == 405


@pytest.mark.django_db
class TestGetResumoProjetoView:

    def test_retorna_200_para_projeto_existente(self):
        projeto = baker.make('api.Projeto')
        factory = RequestFactory()
        request = factory.get(f'/projetos/{projeto.id}/resumo/')
        response = get_resumo_projeto_view(request, projeto.id)
        assert response.status_code == 200

    def test_retorna_405_para_post(self):
        factory = RequestFactory()
        request = factory.post('/projetos/1/resumo/')
        response = get_resumo_projeto_view(request, 1)
        assert response.status_code == 405