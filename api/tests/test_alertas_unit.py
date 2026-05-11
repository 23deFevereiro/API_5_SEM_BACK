import pytest
from model_bakery import baker

from api.services.alertas_svc import get_alertas_materiais, PENDENTE_STATUS


def make_tempo(data_str, pk=None):
    ano, mes, dia = data_str.split('-')
    pk = pk or int(data_str.replace('-', ''))
    return baker.make(
        'api.DimTempo',
        id=pk,
        data=data_str,
        ano=int(ano),
        mes=int(mes),
        trimestre=1,
        semestre=1,
        dia_semana=0,
    )


@pytest.mark.django_db
class TestGetAlertasMateriais:

    def test_retorna_listas_vazias_sem_dados(self):
        resultado = get_alertas_materiais()
        assert resultado == {'criticos': [], 'atencao': []}

    def test_retorna_listas_vazias_sem_empenho(self):
        make_tempo('2024-01-01')
        resultado = get_alertas_materiais()
        assert resultado == {'criticos': [], 'atencao': []}

    def test_retorna_listas_vazias_sem_lead_time_historico(self):
        material = baker.make('api.DimMaterial')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor')
        t1 = make_tempo('2024-01-01')
        t2 = make_tempo('2024-03-31')
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=10)
        baker.make('api.FatoEstoque', material=material, projeto=projeto, tempo=t2,
                   quantidade_estoque=5)

        status_pendente = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_pendente, lead_time=None,
                   quantidade_solicitada=10, quantidade_entregue=0)
        resultado = get_alertas_materiais()
        assert resultado == {'criticos': [], 'atencao': []}

    def test_classifica_material_critico(self):
        """Consumo=1/dia, estoque=5, lead time=2 → cobertura=5, dias_para_pedir=3 → crítico."""
        material = baker.make('api.DimMaterial', descricao='Sensor')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor', razao_social='Fornecedor A')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=5)
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=2,
                   quantidade_solicitada=10, quantidade_entregue=10)
        resultado = get_alertas_materiais()
        assert len(resultado['criticos']) == 1
        assert resultado['atencao'] == []
        item = resultado['criticos'][0]
        assert item['material'] == 'Sensor'
        assert item['fornecedor'] == 'Fornecedor A'
        assert item['dias_para_pedir'] == 3
        assert item['lead_time_min'] == 2

    def test_classifica_material_atencao(self):
        """Consumo=1/dia, estoque=50, lead time=10 → cobertura=50, dias_para_pedir=40 → atenção."""
        material = baker.make('api.DimMaterial', descricao='Resistor')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor', razao_social='Fornecedor B')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=50)
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=10,
                   quantidade_solicitada=10, quantidade_entregue=10)
        resultado = get_alertas_materiais()
        assert resultado['criticos'] == []
        assert len(resultado['atencao']) == 1
        assert resultado['atencao'][0]['material'] == 'Resistor'
        assert resultado['atencao'][0]['dias_para_pedir'] == 40

    def test_nao_classifica_material_confortavel(self):
        """Consumo=1/dia, estoque=100, lead time=10 → dias_para_pedir=90 → nenhuma categoria."""
        material = baker.make('api.DimMaterial')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=100)
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=10,
                   quantidade_solicitada=10, quantidade_entregue=10)
        resultado = get_alertas_materiais()
        assert resultado == {'criticos': [], 'atencao': []}

    def test_pedidos_pendentes_aumentam_cobertura(self):
        """Estoque 0 + pedido pendente de 10 unidades → cobertura=10, dias_para_pedir=8."""
        material = baker.make('api.DimMaterial', descricao='Diodo')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor', razao_social='Fornecedor C')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=0)
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=2,
                   quantidade_solicitada=10, quantidade_entregue=10)
        status_aberto = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_aberto, lead_time=None,
                   quantidade_solicitada=10, quantidade_entregue=0)
        resultado = get_alertas_materiais()
        assert len(resultado['criticos']) == 1
        assert resultado['criticos'][0]['dias_para_pedir'] == 8

    def test_ignora_pedidos_cancelados(self):
        """Pedidos cancelados não devem aumentar a quantidade pendente."""
        material = baker.make('api.DimMaterial', descricao='Transistor')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=5)
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=2,
                   quantidade_solicitada=10, quantidade_entregue=10)
        status_cancel = baker.make('api.DimStatusPedido', nome_status='Cancelado', categoria='Cancelado')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_cancel, lead_time=None,
                   quantidade_solicitada=100, quantidade_entregue=0)
        resultado = get_alertas_materiais()
        assert len(resultado['criticos']) == 1
        assert resultado['criticos'][0]['dias_para_pedir'] == 3

    def test_usa_fornecedor_de_menor_lead_time(self):
        """Deve selecionar o fornecedor com menor lead time médio."""
        material = baker.make('api.DimMaterial', descricao='LED')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor_lento = baker.make('api.DimFornecedor', razao_social='Lento')
        fornecedor_rapido = baker.make('api.DimFornecedor', razao_social='Rápido')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=5)
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor_lento,
                   tempo=t1, status=status_ok, lead_time=10,
                   quantidade_solicitada=10, quantidade_entregue=10)
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor_rapido,
                   tempo=t1, status=status_ok, lead_time=2,
                   quantidade_solicitada=10, quantidade_entregue=10)
        resultado = get_alertas_materiais()
        assert resultado['criticos'][0]['fornecedor'] == 'Rápido'
        assert resultado['criticos'][0]['lead_time_min'] == 2

    def test_limita_criticos_a_5(self):
        """Nunca deve retornar mais de 5 materiais críticos."""
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        for i in range(7):
            material = baker.make('api.DimMaterial', descricao=f'Mat{i}')
            projeto = baker.make('api.DimProjeto')
            programa = baker.make('api.DimPrograma')
            fornecedor = baker.make('api.DimFornecedor')
            t1 = make_tempo(f'2024-01-0{i + 1}', pk=20240100 + i)
            t2 = make_tempo(f'2024-01-1{i + 1}', pk=20240110 + i)
            baker.make('api.FatoMateriais', material=material, projeto=projeto,
                       programa=programa, tempo=t1, quantidade_empenhada=10)
            baker.make('api.FatoEstoque', material=material, projeto=projeto,
                       tempo=t2, quantidade_estoque=5)
            baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                       tempo=t1, status=status_ok, lead_time=2,
                       quantidade_solicitada=10, quantidade_entregue=10)
        resultado = get_alertas_materiais()
        assert len(resultado['criticos']) <= 5

    def test_limita_atencao_a_5(self):
        """Nunca deve retornar mais de 5 materiais em atenção."""
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        for i in range(7):
            material = baker.make('api.DimMaterial', descricao=f'Mat{i}')
            projeto = baker.make('api.DimProjeto')
            programa = baker.make('api.DimPrograma')
            fornecedor = baker.make('api.DimFornecedor')
            t1 = make_tempo(f'2024-01-0{i + 1}', pk=20240100 + i)
            t2 = make_tempo(f'2024-01-1{i + 1}', pk=20240110 + i)
            baker.make('api.FatoMateriais', material=material, projeto=projeto,
                       programa=programa, tempo=t1, quantidade_empenhada=10)
            baker.make('api.FatoEstoque', material=material, projeto=projeto,
                       tempo=t2, quantidade_estoque=50)
            baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                       tempo=t1, status=status_ok, lead_time=10,
                       quantidade_solicitada=10, quantidade_entregue=10)
        resultado = get_alertas_materiais()
        assert len(resultado['atencao']) <= 5

    def test_criticos_ordenados_do_mais_urgente(self):
        """Críticos devem estar ordenados pelo menor dias_para_pedir."""
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        mat_urgente = baker.make('api.DimMaterial', descricao='Urgente')
        mat_menos = baker.make('api.DimMaterial', descricao='MenosUrgente')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=mat_urgente, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=mat_urgente, projeto=projeto,
                   tempo=t1, quantidade_estoque=2)
        baker.make('api.FatoCompras', material=mat_urgente, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=1,
                   quantidade_solicitada=10, quantidade_entregue=10)
        baker.make('api.FatoMateriais', material=mat_menos, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=mat_menos, projeto=projeto,
                   tempo=t1, quantidade_estoque=10)
        baker.make('api.FatoCompras', material=mat_menos, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=1,
                   quantidade_solicitada=10, quantidade_entregue=10)
        resultado = get_alertas_materiais()
        assert resultado['criticos'][0]['material'] == 'Urgente'
        assert resultado['criticos'][1]['material'] == 'MenosUrgente'

    def test_pendente_status_constante_contem_statuses_corretos(self):
        assert 'Aberto' in PENDENTE_STATUS
        assert 'Enviado' in PENDENTE_STATUS
        assert 'Parcialmente Entregue' in PENDENTE_STATUS
        assert 'Cancelado' not in PENDENTE_STATUS
        assert 'Entregue' not in PENDENTE_STATUS

    def test_usa_lead_time_de_pedido_nao_cancelado(self):
        """Lead_time de pedido 'Aberto' (não Cancelado) deve ser considerado no cálculo."""
        material = baker.make('api.DimMaterial', descricao='Componente X')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor', razao_social='Forn Aberto')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=5)
        # Pedido Aberto (Pendente) com lead_time preenchido — antes era ignorado
        status_aberto = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_aberto, lead_time=2,
                   quantidade_solicitada=10, quantidade_entregue=0)
        resultado = get_alertas_materiais()
        # Consumo=1/d, estoque=5, pendente=10, cobertura=15, lt=2 → pedir_em=13 → crítico
        assert len(resultado['criticos']) == 1
        assert resultado['criticos'][0]['lead_time_min'] == 2
        assert resultado['criticos'][0]['fornecedor'] == 'Forn Aberto'

    def test_ignora_lead_time_de_pedido_cancelado(self):
        """Pedido Cancelado com lead_time NÃO deve entrar no cálculo."""
        material = baker.make('api.DimMaterial', descricao='Sem LT')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=5)
        # Apenas pedido Cancelado com lead_time — deve ser excluído
        status_cancel = baker.make('api.DimStatusPedido', nome_status='Cancelado', categoria='Cancelado')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_cancel, lead_time=5,
                   quantidade_solicitada=10, quantidade_entregue=0)
        resultado = get_alertas_materiais()
        assert resultado == {'criticos': [], 'atencao': []}

    def test_parametro_critico_max_personalizado(self):
        """Com critico_max=90, material com dias_para_pedir=70 deve ser classificado como crítico."""
        material = baker.make('api.DimMaterial', descricao='CompX')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor', razao_social='FornX')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=80)
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=10,
                   quantidade_solicitada=10, quantidade_entregue=10)
        # dias_para_pedir = 80 - 10 = 70 → padrão (30): confortável; com critico_max=90: crítico
        assert get_alertas_materiais() == {'criticos': [], 'atencao': []}
        resultado = get_alertas_materiais(critico_max=90, atencao_max=120)
        assert len(resultado['criticos']) == 1
        assert resultado['criticos'][0]['material'] == 'CompX'

    def test_parametro_atencao_max_personalizado(self):
        """Com atencao_max=120, material com dias_para_pedir=100 deve entrar em atenção."""
        material = baker.make('api.DimMaterial', descricao='CompY')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor', razao_social='FornY')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=110)
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=10,
                   quantidade_solicitada=10, quantidade_entregue=10)
        # dias_para_pedir = 110 - 10 = 100 → padrão (60): confortável; com atencao_max=120: atenção
        assert get_alertas_materiais() == {'criticos': [], 'atencao': []}
        resultado = get_alertas_materiais(critico_max=30, atencao_max=120)
        assert len(resultado['atencao']) == 1
        assert resultado['atencao'][0]['material'] == 'CompY'
