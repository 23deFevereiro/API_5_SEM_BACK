import pytest
from pytest import approx
from model_bakery import baker
from datetime import date

from api.services.compras_svc import listar_materiais_com_compras, get_lead_time_por_material, get_sugestao_proxima_compra


@pytest.mark.django_db
class TestListarMateriaisComCompras:

    def test_retorna_lista_vazia_sem_dados(self):
        resultado = listar_materiais_com_compras()
        assert resultado == []

    def test_retorna_material_com_compras(self):
        material = baker.make('api.DimMaterial', codigo_material='M001', descricao='Capacitor')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        status = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=tempo, status=status, lead_time=10)
        resultado = listar_materiais_com_compras()
        assert len(resultado) == 1
        assert resultado[0]['id'] == material.id
        assert resultado[0]['codigo_material'] == 'M001'
        assert resultado[0]['descricao'] == 'Capacitor'

    def test_nao_retorna_material_sem_fatos(self):
        baker.make('api.DimMaterial', codigo_material='SEM', descricao='Sem compra')
        resultado = listar_materiais_com_compras()
        assert resultado == []

    def test_retorna_material_apenas_em_fatomateriais(self):
        material = baker.make('api.DimMaterial', codigo_material='M002', descricao='Resistor')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=5)
        resultado = listar_materiais_com_compras()
        assert len(resultado) == 1
        assert resultado[0]['id'] == material.id
        assert resultado[0]['codigo_material'] == 'M002'
        assert resultado[0]['descricao'] == 'Resistor'

    def test_nao_duplica_material_em_ambas_as_tabelas(self):
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        projeto = baker.make('api.DimProjeto')
        programa = baker.make('api.DimPrograma')
        tempo = baker.make('api.DimTempo')
        status = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=tempo, status=status, lead_time=5)
        baker.make('api.FatoMateriais', material=material, projeto=projeto,
                   programa=programa, fornecedor=fornecedor, tempo=tempo,
                   quantidade_empenhada=3)
        resultado = listar_materiais_com_compras()
        assert len(resultado) == 1

    def test_nao_duplica_material_com_multiplas_compras(self):
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        status = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        tempo1 = baker.make('api.DimTempo', id=20240101, data='2024-01-01',
                            ano=2024, mes=1, trimestre=1, semestre=1, dia_semana=0)
        tempo2 = baker.make('api.DimTempo', id=20240201, data='2024-02-01',
                            ano=2024, mes=2, trimestre=1, semestre=1, dia_semana=3)
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=tempo1, status=status, lead_time=5)
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=tempo2, status=status, lead_time=8)
        resultado = listar_materiais_com_compras()
        assert len(resultado) == 1

    def test_retorna_campos_id_codigo_descricao(self):
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        status = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=tempo, status=status, lead_time=10)
        resultado = listar_materiais_com_compras()
        assert set(resultado[0].keys()) == {'id', 'codigo_material', 'descricao'}

    def test_retorna_ordenado_por_descricao(self):
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        status = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        mat_z = baker.make('api.DimMaterial', descricao='Zener')
        mat_a = baker.make('api.DimMaterial', descricao='Ampere')
        baker.make('api.FatoCompras', material=mat_z, fornecedor=fornecedor,
                   tempo=tempo, status=status, lead_time=5)
        baker.make('api.FatoCompras', material=mat_a, fornecedor=fornecedor,
                   tempo=tempo, status=status, lead_time=5)
        resultado = listar_materiais_com_compras()
        assert resultado[0]['descricao'] == 'Ampere'
        assert resultado[1]['descricao'] == 'Zener'


@pytest.mark.django_db
class TestGetLeadTimePorMaterial:

    def _criar_compra(self, material, fornecedor_nome='Fornecedor A', lead_time=15,
                      valor_total=1000.0, quantidade=10, status_nome='Entregue',
                      categoria='Concluído', data='2024-01-01', tempo_id=20240101,
                      projeto=None):
        fornecedor = baker.make('api.DimFornecedor', razao_social=fornecedor_nome)
        status = baker.make('api.DimStatusPedido', nome_status=status_nome, categoria=categoria)
        tempo = baker.make('api.DimTempo', id=tempo_id, data=data, ano=int(data[:4]),
                           mes=int(data[5:7]), trimestre=1, semestre=1, dia_semana=0)
        return baker.make(
            'api.FatoCompras',
            material=material,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=lead_time,
            valor_total=valor_total,
            quantidade_solicitada=quantidade,
            projeto=projeto,
        )

    def test_retorna_lista_vazia_sem_compras(self):
        material = baker.make('api.DimMaterial')
        resultado = get_lead_time_por_material(material.id)
        assert resultado == []

    def test_retorna_lista_vazia_para_material_inexistente(self):
        resultado = get_lead_time_por_material(99999)
        assert resultado == []

    def test_exclui_compras_sem_lead_time(self):
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor')
        tempo = baker.make('api.DimTempo')
        status = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=tempo, status=status, lead_time=None)
        resultado = get_lead_time_por_material(material.id)
        assert resultado == []

    def test_retorna_campos_corretos(self):
        material = baker.make('api.DimMaterial')
        self._criar_compra(material, fornecedor_nome='Fornecedor X', lead_time=20,
                           valor_total=500.0, quantidade=5)
        resultado = get_lead_time_por_material(material.id)
        assert len(resultado) == 1
        ponto = resultado[0]
        assert ponto['fornecedor'] == 'Fornecedor X'
        assert ponto['lead_time'] == 20
        assert ponto['valor_total'] == approx(500.0)
        assert ponto['status'] == 'Entregue'
        assert ponto['categoria_status'] == 'Concluído'
        assert ponto['data_pedido'] == '2024-01-01'

    def test_calcula_valor_unidade_corretamente(self):
        material = baker.make('api.DimMaterial')
        self._criar_compra(material, valor_total=1000.0, quantidade=4)
        resultado = get_lead_time_por_material(material.id)
        assert resultado[0]['valor_unidade'] == approx(250.0)

    def test_quantidade_zero_usa_1_para_evitar_divisao_por_zero(self):
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor', razao_social='F')
        status = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        tempo = baker.make('api.DimTempo', id=20240301, data='2024-03-01',
                           ano=2024, mes=3, trimestre=1, semestre=1, dia_semana=4)
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor,
                   tempo=tempo, status=status, lead_time=10, valor_total=300.0,
                   quantidade_solicitada=0)
        resultado = get_lead_time_por_material(material.id)
        assert resultado[0]['valor_unidade'] == approx(300.0)

    def test_deduplica_compras_de_mesmo_pedido_em_projetos_diferentes(self):
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor', razao_social='Dup Ltda')
        status = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        tempo = baker.make('api.DimTempo', id=20241208, data='2024-12-08',
                           ano=2024, mes=12, trimestre=4, semestre=2, dia_semana=6)
        projeto1 = baker.make('api.DimProjeto')
        projeto2 = baker.make('api.DimProjeto')
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor, tempo=tempo,
                   status=status, lead_time=25, valor_total=1000.0,
                   quantidade_solicitada=10, projeto=projeto1)
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor, tempo=tempo,
                   status=status, lead_time=25, valor_total=1000.0,
                   quantidade_solicitada=10, projeto=projeto2)
        resultado = get_lead_time_por_material(material.id)
        assert len(resultado) == 1

    def test_nao_deduplica_compras_diferentes(self):
        material = baker.make('api.DimMaterial')
        fornecedor = baker.make('api.DimFornecedor', razao_social='F1')
        status = baker.make('api.DimStatusPedido', nome_status='Aberto', categoria='Pendente')
        tempo1 = baker.make('api.DimTempo', id=20240101, data='2024-01-01',
                            ano=2024, mes=1, trimestre=1, semestre=1, dia_semana=0)
        tempo2 = baker.make('api.DimTempo', id=20240201, data='2024-02-01',
                            ano=2024, mes=2, trimestre=1, semestre=1, dia_semana=3)
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor, tempo=tempo1,
                   status=status, lead_time=10, valor_total=500.0, quantidade_solicitada=5)
        baker.make('api.FatoCompras', material=material, fornecedor=fornecedor, tempo=tempo2,
                   status=status, lead_time=20, valor_total=800.0, quantidade_solicitada=8)
        resultado = get_lead_time_por_material(material.id)
        assert len(resultado) == 2

    def test_nao_retorna_dados_de_outro_material(self):
        mat1 = baker.make('api.DimMaterial')
        mat2 = baker.make('api.DimMaterial')
        self._criar_compra(mat2, tempo_id=20240501, data='2024-05-01')
        resultado = get_lead_time_por_material(mat1.id)
        assert resultado == []
        
@pytest.mark.django_db
class TestGetSugestaoProximaCompra:

    def _criar_tempo(self, data, tempo_id):
        return baker.make(
            'api.DimTempo',
            id=tempo_id,
            data=data,
            ano=data.year,
            mes=data.month,
            trimestre=1,
            semestre=1,
            dia_semana=0,
        )

    def test_retorna_vazio_sem_consumo(self):
        resultado = get_sugestao_proxima_compra(
            data_referencia=date(2024, 1, 10)
        )

        assert resultado['data_sugerida'] is None
        assert resultado['comprar_imediatamente'] is False
        assert resultado['materiais'] == []

    def test_recomenda_compra_com_lead_time_do_fornecedor(self):
        material = baker.make(
            'api.DimMaterial',
            codigo_material='MAT-001',
            descricao='Parafuso',
        )
        fornecedor = baker.make(
            'api.DimFornecedor',
            razao_social='Fornecedor Alpha',
        )
        status = baker.make(
            'api.DimStatusPedido',
            nome_status='Entregue',
            categoria='Concluído',
        )
        tempo_consumo = self._criar_tempo(date(2024, 1, 1), 20240101)
        tempo_estoque = self._criar_tempo(date(2024, 1, 10), 20240110)

        baker.make(
            'api.FatoMateriais',
            material=material,
            tempo=tempo_consumo,
            quantidade_empenhada=100,
        )
        baker.make(
            'api.FatoEstoque',
            material=material,
            tempo=tempo_estoque,
            quantidade_estoque=20,
        )
        baker.make(
            'api.FatoCompras',
            material=material,
            fornecedor=fornecedor,
            tempo=tempo_consumo,
            status=status,
            lead_time=5,
            quantidade_solicitada=100,
            quantidade_entregue=100,
            valor_total=1000,
        )

        resultado = get_sugestao_proxima_compra(
            data_referencia=date(2024, 1, 10)
        )

        assert resultado['materiais']
        assert resultado['comprar_imediatamente'] is True

        item = resultado['materiais'][0]
        assert item['material'] == 'Parafuso'
        assert item['fornecedor_sugerido'] == 'Fornecedor Alpha'
        assert item['lead_time'] == 5
        assert item['comprar_imediatamente'] is True

    def test_usa_lead_time_padrao_sem_compra_com_lead_time(self):
        material = baker.make(
            'api.DimMaterial',
            codigo_material='MAT-002',
            descricao='Cabo',
        )
        tempo_consumo = self._criar_tempo(date(2024, 1, 1), 20240201)
        tempo_estoque = self._criar_tempo(date(2024, 1, 10), 20240210)

        baker.make(
            'api.FatoMateriais',
            material=material,
            tempo=tempo_consumo,
            quantidade_empenhada=100,
        )
        baker.make(
            'api.FatoEstoque',
            material=material,
            tempo=tempo_estoque,
            quantidade_estoque=10,
        )

        resultado = get_sugestao_proxima_compra(
            data_referencia=date(2024, 1, 10)
        )

        item = resultado['materiais'][0]
        assert item['lead_time'] == 30
        assert item['fornecedor_sugerido'] == 'Fornecedor não definido'

    def test_ignora_material_com_cobertura_maior_que_limite(self):
        material = baker.make(
            'api.DimMaterial',
            codigo_material='MAT-003',
            descricao='Motor',
        )
        tempo_consumo = self._criar_tempo(date(2024, 1, 1), 20240301)
        tempo_estoque = self._criar_tempo(date(2024, 1, 10), 20240310)

        baker.make(
            'api.FatoMateriais',
            material=material,
            tempo=tempo_consumo,
            quantidade_empenhada=10,
        )
        baker.make(
            'api.FatoEstoque',
            material=material,
            tempo=tempo_estoque,
            quantidade_estoque=1000,
        )

        resultado = get_sugestao_proxima_compra(
            data_referencia=date(2024, 1, 10)
        )

        assert resultado['materiais'] == []
        assert resultado['comprar_imediatamente'] is False