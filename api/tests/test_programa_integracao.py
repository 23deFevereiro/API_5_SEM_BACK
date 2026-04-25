import pytest
from pytest import approx
from model_bakery import baker
from api.services.programa_svc import listar_programas, get_resumo_programa, get_distribuicao_status
from model_bakery.recipe import seq


@pytest.mark.django_db
class TestListarProgramas:

    def test_retorna_lista_vazia_quando_nao_ha_programas(self):
        resultado = listar_programas()
        assert resultado == []

    def test_retorna_programas_quando_existem(self):
        baker.make('api.Programa', nome_programa=seq('Programa Alpha '), _quantity=3)
        resultado = listar_programas()
        assert len(resultado) == 3

    def test_filtra_por_nome_quando_search_informado(self):
        baker.make('api.Programa', nome_programa='Programa Alpha')
        baker.make('api.Programa', nome_programa='Programa Beta')
        resultado = listar_programas(search='Alpha')
        assert len(resultado) == 1
        assert resultado[0]['nome_programa'] == 'Programa Alpha'

    def test_retorna_campos_corretos(self):
        baker.make('api.Programa', nome_programa='Teste')
        resultado = listar_programas()
        assert 'id' in resultado[0]
        assert 'codigo_programa' in resultado[0]
        assert 'nome_programa' in resultado[0]


@pytest.mark.django_db
class TestGetResumoProjeto:

    def test_retorna_zeros_quando_programa_sem_dados(self):
        programa = baker.make('api.Programa')
        resultado = get_resumo_programa(programa.id)
        assert resultado['total_projetos'] == 0
        assert resultado['horas_estimadas'] == approx(0.0)
        assert resultado['horas_realizadas'] == approx(0.0)
        assert resultado['custo_estimado'] == approx(0.0)
        assert resultado['custo_real'] == approx(0.0)

    def test_conta_total_projetos_corretamente(self):
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa, _quantity=3)
        resultado = get_resumo_programa(programa.id)
        assert resultado['total_projetos'] == 3

    def test_calcula_horas_estimadas_corretamente(self):
        programa = baker.make('api.Programa')
        projeto = baker.make('api.Projeto', programa=programa)
        baker.make('api.Tarefa', projeto=projeto, estimativa_horas=10.0)
        baker.make('api.Tarefa', projeto=projeto, estimativa_horas=5.0)
        resultado = get_resumo_programa(programa.id)
        assert resultado['horas_estimadas'] == approx(15.0)

    def test_calcula_horas_realizadas_corretamente(self):
        programa = baker.make('api.Programa')
        projeto = baker.make('api.Projeto', programa=programa)
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, horas_trabalhadas=8.0)
        baker.make('api.TempoTarefa', tarefa=tarefa, horas_trabalhadas=4.0)
        resultado = get_resumo_programa(programa.id)
        assert resultado['horas_realizadas'] == approx(12.0)

    def test_calcula_custo_estimado_mao_de_obra(self):
        programa = baker.make('api.Programa')
        projeto = baker.make('api.Projeto', programa=programa, custo_hora=50.00)
        baker.make('api.Tarefa', projeto=projeto, estimativa_horas=10.0)
        resultado = get_resumo_programa(programa.id)
        assert resultado['custo_estimado'] == approx(500.0)

    def test_calcula_custo_estimado_materiais(self):
        programa = baker.make('api.Programa')
        projeto = baker.make('api.Projeto', programa=programa, custo_hora=0)
        material = baker.make('api.Material', custo_estimado=100.00)
        baker.make('api.EmpenhoMaterial', projeto=projeto, material=material, quantidade_empenhada=5)
        resultado = get_resumo_programa(programa.id)
        assert resultado['custo_estimado'] == approx(500.0)

    def test_calcula_custo_real_mao_de_obra(self):
        programa = baker.make('api.Programa')
        projeto = baker.make('api.Projeto', programa=programa, custo_hora=50.00)
        tarefa = baker.make('api.Tarefa', projeto=projeto)
        baker.make('api.TempoTarefa', tarefa=tarefa, horas_trabalhadas=10.0)
        resultado = get_resumo_programa(programa.id)
        assert resultado['custo_real'] == approx(500.0)

    def test_exclui_compras_canceladas_do_custo_real(self):
        programa = baker.make('api.Programa')
        projeto = baker.make('api.Projeto', programa=programa, custo_hora=0)
        pedido_cancelado = baker.make('api.PedidoCompra', status='Cancelado')
        pedido_ativo = baker.make('api.PedidoCompra', status='Entregue')
        baker.make('api.ComprasProjeto', projeto=projeto, pedido_compra=pedido_cancelado, valor_alocado=1000.00)
        baker.make('api.ComprasProjeto', projeto=projeto, pedido_compra=pedido_ativo, valor_alocado=500.00)
        resultado = get_resumo_programa(programa.id)
        assert resultado['custo_real'] == approx(500.0)

    def test_nao_inclui_dados_de_outro_programa(self):
        programa1 = baker.make('api.Programa')
        programa2 = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa2, _quantity=5)
        resultado = get_resumo_programa(programa1.id)
        assert resultado['total_projetos'] == 0


@pytest.mark.django_db
class TestGetDistribuicaoStatus:

    def test_retorna_total_zero_quando_programa_sem_projetos(self):
        programa = baker.make('api.Programa')
        resultado = get_distribuicao_status(programa.id)
        assert resultado['total'] == 0
        assert resultado['status'] == []

    def test_retorna_apenas_status_com_projetos(self):
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa, status='Planejamento', _quantity=3)
        resultado = get_distribuicao_status(programa.id)
        assert len(resultado['status']) == 1
        assert resultado['status'][0]['status'] == 'Planejamento'

    def test_conta_total_corretamente(self):
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa, status='Planejamento', _quantity=4)
        baker.make('api.Projeto', programa=programa, status='Concluído', _quantity=6)
        resultado = get_distribuicao_status(programa.id)
        assert resultado['total'] == 10

    def test_calcula_percentual_corretamente(self):
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa, status='Planejamento', _quantity=1)
        baker.make('api.Projeto', programa=programa, status='Concluído', _quantity=3)
        resultado = get_distribuicao_status(programa.id)
        status_dict = {s['status']: s for s in resultado['status']}
        assert status_dict['Planejamento']['percentual'] == 25.0
        assert status_dict['Concluído']['percentual'] == 75.0

    def test_retorna_quantidade_absoluta_corretamente(self):
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa, status='Em andamento', _quantity=5)
        resultado = get_distribuicao_status(programa.id)
        assert resultado['status'][0]['quantidade'] == 5

    def test_retorna_cor_correta_por_status(self):
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa, status='Planejamento')
        baker.make('api.Projeto', programa=programa, status='Em andamento')
        baker.make('api.Projeto', programa=programa, status='Suspenso')
        baker.make('api.Projeto', programa=programa, status='Concluído')
        resultado = get_distribuicao_status(programa.id)
        status_dict = {s['status']: s for s in resultado['status']}
        assert status_dict['Planejamento']['cor'] == '#3B82F6'
        assert status_dict['Em andamento']['cor'] == '#EAB308'
        assert status_dict['Suspenso']['cor'] == '#F97316'
        assert status_dict['Concluído']['cor'] == '#22C55E'

    def test_nao_inclui_projetos_de_outro_programa(self):
        programa1 = baker.make('api.Programa')
        programa2 = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa2, status='Planejamento', _quantity=5)
        resultado = get_distribuicao_status(programa1.id)
        assert resultado['total'] == 0
        assert resultado['status'] == []

    def test_retorna_todos_os_quatro_status_quando_presentes(self):
        programa = baker.make('api.Programa')
        baker.make('api.Projeto', programa=programa, status='Planejamento', _quantity=2)
        baker.make('api.Projeto', programa=programa, status='Em andamento', _quantity=3)
        baker.make('api.Projeto', programa=programa, status='Suspenso', _quantity=1)
        baker.make('api.Projeto', programa=programa, status='Concluído', _quantity=4)
        resultado = get_distribuicao_status(programa.id)
        assert len(resultado['status']) == 4
        assert resultado['total'] == 10