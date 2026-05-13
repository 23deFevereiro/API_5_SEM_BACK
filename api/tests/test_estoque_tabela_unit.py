import pytest
from model_bakery import baker

from api.services.alertas_svc import get_estoque_tabela


def make_tempo(data_str, pk=None):
    ano, mes, _ = data_str.split('-')
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
class TestGetEstoqueTabela:

    def test_retorna_vazio_sem_dados(self):
        resultado = get_estoque_tabela()
        assert resultado['count'] == 0
        assert resultado['results'] == []

    def test_retorna_vazio_sem_empenho(self):
        make_tempo('2024-01-01')
        resultado = get_estoque_tabela()
        assert resultado['count'] == 0

    def test_retorna_material_com_status_ok_sem_lead_time(self):
        """Material sem lead_time histórico com cobertura suficiente → status Ok."""
        material = baker.make('api.DimMaterial', descricao='Capacitor')
        projeto = baker.make('api.DimProjeto', nome_projeto='Projeto Alpha')
        programa = baker.make('api.DimPrograma')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=10)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=700)  # 700/10 = 70 dias > atencao_max=60
        resultado = get_estoque_tabela()
        assert resultado['count'] == 1
        item = resultado['results'][0]
        assert item['material'] == 'Capacitor'
        assert item['projeto'] == 'Projeto Alpha'
        assert item['estoque_atual'] == 700
        assert item['status'] == 'Ok'

    def test_status_urgente_quando_dias_para_pedir_menor_que_critico_max(self):
        """Consumo=1/dia, estoque=5, lead_time=2 → cobertura=5, dias_para_pedir=3 → Urgente."""
        material = baker.make('api.DimMaterial', descricao='Sensor')
        projeto = baker.make('api.DimProjeto', nome_projeto='Projeto Beta')
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
        resultado = get_estoque_tabela(critico_max=30)
        assert resultado['results'][0]['status'] == 'Urgente'

    def test_status_atencao_quando_dias_entre_limiares(self):
        """Consumo=1/dia, estoque=50, lead_time=10 → dias_para_pedir=40 → Atenção."""
        material = baker.make('api.DimMaterial', descricao='Resistor')
        projeto = baker.make('api.DimProjeto', nome_projeto='Projeto Gama')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=50)
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=10,
                   quantidade_solicitada=10, quantidade_entregue=10)
        resultado = get_estoque_tabela(critico_max=30, atencao_max=60)
        assert resultado['results'][0]['status'] == 'Atenção'

    def test_status_ok_quando_dias_acima_de_atencao_max(self):
        """Consumo=1/dia, estoque=100, lead_time=10 → dias_para_pedir=90 → Ok."""
        material = baker.make('api.DimMaterial', descricao='LED')
        projeto = baker.make('api.DimProjeto', nome_projeto='Projeto Delta')
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
        resultado = get_estoque_tabela(critico_max=30, atencao_max=60)
        assert resultado['results'][0]['status'] == 'Ok'

    def test_ordenacao_urgente_antes_de_atencao_antes_de_ok(self):
        """Urgente deve aparecer antes de Atenção que deve aparecer antes de Ok."""
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor')
        t1 = make_tempo('2024-01-01', pk=20240101)
        status_ok = baker.make('api.DimStatusPedido', nome_status='Entregue', categoria='Concluído')

        mat_ok = baker.make('api.DimMaterial', descricao='AAA-Ok')
        baker.make('api.FatoMateriais', material=mat_ok, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=mat_ok, projeto=projeto,
                   tempo=t1, quantidade_estoque=100)
        baker.make('api.FatoCompras', material=mat_ok, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=10,
                   quantidade_solicitada=10, quantidade_entregue=10)

        mat_atencao = baker.make('api.DimMaterial', descricao='AAA-Atencao')
        baker.make('api.FatoMateriais', material=mat_atencao, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=mat_atencao, projeto=projeto,
                   tempo=t1, quantidade_estoque=50)
        baker.make('api.FatoCompras', material=mat_atencao, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=10,
                   quantidade_solicitada=10, quantidade_entregue=10)

        mat_urgente = baker.make('api.DimMaterial', descricao='AAA-Urgente')
        baker.make('api.FatoMateriais', material=mat_urgente, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        baker.make('api.FatoEstoque', material=mat_urgente, projeto=projeto,
                   tempo=t1, quantidade_estoque=5)
        baker.make('api.FatoCompras', material=mat_urgente, fornecedor=fornecedor,
                   tempo=t1, status=status_ok, lead_time=2,
                   quantidade_solicitada=10, quantidade_entregue=10)

        resultado = get_estoque_tabela(critico_max=30, atencao_max=60, page_size=10)
        statuses = [r['status'] for r in resultado['results']]
        assert statuses.index('Urgente') < statuses.index('Atenção')
        assert statuses.index('Atenção') < statuses.index('Ok')

    def test_paginacao_page_1(self):
        """Com 6 materiais e page_size=5, página 1 retorna 5 itens."""
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        t1 = make_tempo('2024-01-01', pk=20240101)
        for i in range(6):
            mat = baker.make('api.DimMaterial', descricao=f'Mat{i:02d}')
            baker.make('api.FatoMateriais', material=mat, projeto=projeto,
                       programa=programa, tempo=t1, quantidade_empenhada=1)
        resultado = get_estoque_tabela(page=1, page_size=5)
        assert resultado['count'] == 6
        assert resultado['total_pages'] == 2
        assert len(resultado['results']) == 5
        assert resultado['page'] == 1

    def test_paginacao_page_2(self):
        """Com 6 materiais e page_size=5, página 2 retorna 1 item."""
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        t1 = make_tempo('2024-01-01', pk=20240101)
        for i in range(6):
            mat = baker.make('api.DimMaterial', descricao=f'Mat{i:02d}')
            baker.make('api.FatoMateriais', material=mat, projeto=projeto,
                       programa=programa, tempo=t1, quantidade_empenhada=1)
        resultado = get_estoque_tabela(page=2, page_size=5)
        assert len(resultado['results']) == 1
        assert resultado['page'] == 2

    def test_projeto_principal_e_o_de_maior_consumo(self):
        """O projeto com maior consumo do material deve ser exibido."""
        material = baker.make('api.DimMaterial', descricao='Transistor')
        programa = baker.make('api.DimPrograma')
        proj_menor = baker.make('api.DimProjeto', nome_projeto='Projeto Menor')
        proj_maior = baker.make('api.DimProjeto', nome_projeto='Projeto Maior')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=proj_menor,
                   programa=programa, tempo=t1, quantidade_empenhada=2)
        baker.make('api.FatoMateriais', material=material, projeto=proj_maior,
                   programa=programa, tempo=t1, quantidade_empenhada=8)
        resultado = get_estoque_tabela()
        assert resultado['results'][0]['projeto'] == 'Projeto Maior'

    def test_consumo_previsto_e_por_dia(self):
        """consumo_previsto deve ser total_empenhado / dias_periodo."""
        material = baker.make('api.DimMaterial', descricao='Diodo')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        t1 = make_tempo('2024-01-01', pk=20240101)
        t2 = make_tempo('2024-01-10', pk=20240110)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=5)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t2, quantidade_empenhada=5)
        resultado = get_estoque_tabela()
        assert resultado['results'][0]['consumo_previsto'] == pytest.approx(1.0)

    def test_filtra_por_material_id(self):
        """Quando material_id fornecido, apenas esse material é retornado."""
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        t1 = make_tempo('2024-01-01', pk=20240101)
        mat1 = baker.make('api.DimMaterial', descricao='Sensor')
        mat2 = baker.make('api.DimMaterial', descricao='Resistor')
        for mat in [mat1, mat2]:
            baker.make('api.FatoMateriais', material=mat, projeto=projeto,
                       programa=programa, tempo=t1, quantidade_empenhada=1)
        resultado = get_estoque_tabela(material_id=mat1.id)
        assert resultado['count'] == 1
        assert resultado['results'][0]['material'] == 'Sensor'

    def test_material_id_inexistente_retorna_vazio(self):
        """material_id que não existe → lista vazia."""
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        t1 = make_tempo('2024-01-01', pk=20240101)
        mat = baker.make('api.DimMaterial', descricao='Sensor')
        baker.make('api.FatoMateriais', material=mat, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        resultado = get_estoque_tabela(material_id=mat.id + 9999)
        assert resultado['count'] == 0
        assert resultado['results'] == []

    def test_pendente_nao_e_contado_em_dias_ate_acabar(self):
        """Pedidos pendentes não devem inflar dias_ate_acabar nem o status.
        Estoque físico = 0 → dias = 0 → Urgente, mesmo com pendente grande."""
        material = baker.make('api.DimMaterial', descricao='Capacitor')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor')
        t1 = make_tempo('2024-01-01', pk=20240101)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, tempo=t1, quantidade_empenhada=1)
        # estoque físico = 0
        baker.make('api.FatoEstoque', material=material, projeto=projeto,
                   tempo=t1, quantidade_estoque=0)
        # pedido aberto com quantidade alta (pendente = 1000)
        status_aberto = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=t1, status=status_aberto, lead_time=2,
                   quantidade_solicitada=1000, quantidade_entregue=0)
        # lead_time = 2 dias → dias_para_pedir = 0 - 2 = -2 → Urgente
        resultado = get_estoque_tabela(critico_max=30)
        item = resultado['results'][0]
        assert item['dias_ate_acabar'] == 0
        assert item['status'] == 'Urgente'
