import pytest
from model_bakery import baker
from pytest import approx

from api.services.compras_svc import (
    get_lead_time_por_material,
    listar_materiais_com_compras,
)


@pytest.mark.django_db
class TestListarMateriaisComCompras:

    # TC-C01 — Cenário: Nenhum material com compra registrada (camada de serviço)
    def test_retorna_lista_vazia_sem_dados(self):
        resultado = listar_materiais_com_compras()
        assert resultado == []

    # TC-C01 — Cenário: Retornar materiais com compras (camada de serviço)
    def test_retorna_material_com_compras(self):
        material = baker.make(
            "api.DimMaterial", codigo_material="M001", descricao="Capacitor"
        )
        fornecedor = baker.make("api.DimFornecedor")
        tempo = baker.make("api.DimTempo")
        status = baker.make(
            "api.DimStatusPedido", nome_status="Aberto", categoria="Pendente"
        )
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=10,
        )
        resultado = listar_materiais_com_compras()
        assert len(resultado) == 1
        assert resultado[0]["id"] == material.id
        assert resultado[0]["codigo_material"] == "M001"
        assert resultado[0]["descricao"] == "Capacitor"

    # TC-C01 — Cenário: Nenhum material com compra registrada
    # (material sem fatos não aparece)
    def test_nao_retorna_material_sem_fatos(self):
        baker.make("api.DimMaterial", codigo_material="SEM", descricao="Sem compra")
        resultado = listar_materiais_com_compras()
        assert resultado == []

    # Complementar ao TC-C01: material com empenho (FatoMateriais) também é listado
    def test_retorna_material_apenas_em_fatomateriais(self):
        material = baker.make(
            "api.DimMaterial", codigo_material="M002", descricao="Resistor"
        )
        projeto = baker.make("api.DimProjeto")
        programa = baker.make("api.DimPrograma")
        fornecedor = baker.make("api.DimFornecedor")
        tempo = baker.make("api.DimTempo")
        baker.make(
            "api.FatoMateriais",
            material=material,
            projeto=projeto,
            programa=programa,
            fornecedor=fornecedor,
            tempo=tempo,
            quantidade_empenhada=5,
        )
        resultado = listar_materiais_com_compras()
        assert len(resultado) == 1
        assert resultado[0]["id"] == material.id
        assert resultado[0]["codigo_material"] == "M002"
        assert resultado[0]["descricao"] == "Resistor"

    # Complementar ao TC-C01: material presente em compras e empenhos não duplica
    def test_nao_duplica_material_em_ambas_as_tabelas(self):
        material = baker.make("api.DimMaterial")
        fornecedor = baker.make("api.DimFornecedor")
        projeto = baker.make("api.DimProjeto")
        programa = baker.make("api.DimPrograma")
        tempo = baker.make("api.DimTempo")
        status = baker.make(
            "api.DimStatusPedido", nome_status="Aberto", categoria="Pendente"
        )
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=5,
        )
        baker.make(
            "api.FatoMateriais",
            material=material,
            projeto=projeto,
            programa=programa,
            fornecedor=fornecedor,
            tempo=tempo,
            quantidade_empenhada=3,
        )
        resultado = listar_materiais_com_compras()
        assert len(resultado) == 1

    # Complementar ao TC-C01: múltiplas compras do mesmo material não duplicam
    def test_nao_duplica_material_com_multiplas_compras(self):
        material = baker.make("api.DimMaterial")
        fornecedor = baker.make("api.DimFornecedor")
        status = baker.make(
            "api.DimStatusPedido", nome_status="Aberto", categoria="Pendente"
        )
        tempo1 = baker.make(
            "api.DimTempo",
            id=20240101,
            data="2024-01-01",
            ano=2024,
            mes=1,
            trimestre=1,
            semestre=1,
            dia_semana=0,
        )
        tempo2 = baker.make(
            "api.DimTempo",
            id=20240201,
            data="2024-02-01",
            ano=2024,
            mes=2,
            trimestre=1,
            semestre=1,
            dia_semana=3,
        )
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo1,
            status=status,
            lead_time=5,
        )
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo2,
            status=status,
            lead_time=8,
        )
        resultado = listar_materiais_com_compras()
        assert len(resultado) == 1

    # TC-C01 — Contrato: cada item possui id, codigo_material e descricao
    def test_retorna_campos_id_codigo_descricao(self):
        material = baker.make("api.DimMaterial")
        fornecedor = baker.make("api.DimFornecedor")
        tempo = baker.make("api.DimTempo")
        status = baker.make(
            "api.DimStatusPedido", nome_status="Aberto", categoria="Pendente"
        )
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=10,
        )
        resultado = listar_materiais_com_compras()
        assert set(resultado[0].keys()) == {"id", "codigo_material", "descricao"}

    # Complementar ao TC-C01: resultado ordenado por descrição
    def test_retorna_ordenado_por_descricao(self):
        fornecedor = baker.make("api.DimFornecedor")
        tempo = baker.make("api.DimTempo")
        status = baker.make(
            "api.DimStatusPedido", nome_status="Aberto", categoria="Pendente"
        )
        mat_z = baker.make("api.DimMaterial", descricao="Zener")
        mat_a = baker.make("api.DimMaterial", descricao="Ampere")
        baker.make(
            "api.FatoCompras",
            material=mat_z,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=5,
        )
        baker.make(
            "api.FatoCompras",
            material=mat_a,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=5,
        )
        resultado = listar_materiais_com_compras()
        assert resultado[0]["descricao"] == "Ampere"
        assert resultado[1]["descricao"] == "Zener"


@pytest.mark.django_db
class TestGetLeadTimePorMaterial:

    def _criar_compra(
        self,
        material,
        fornecedor_nome="Fornecedor A",
        lead_time=15,
        valor_total=1000.0,
        quantidade=10,
        status_nome="Entregue",
        categoria="Concluído",
        data="2024-01-01",
        tempo_id=20240101,
        projeto=None,
    ):
        fornecedor = baker.make("api.DimFornecedor", razao_social=fornecedor_nome)
        status = baker.make(
            "api.DimStatusPedido", nome_status=status_nome, categoria=categoria
        )
        tempo = baker.make(
            "api.DimTempo",
            id=tempo_id,
            data=data,
            ano=int(data[:4]),
            mes=int(data[5:7]),
            trimestre=1,
            semestre=1,
            dia_semana=0,
        )
        return baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=lead_time,
            valor_total=valor_total,
            quantidade_solicitada=quantidade,
            projeto=projeto,
        )

    # TC-C02 — Cenário: Material sem compras registradas (body [])
    def test_retorna_lista_vazia_sem_compras(self):
        material = baker.make("api.DimMaterial")
        resultado = get_lead_time_por_material(material.id)
        assert resultado == []

    # Complementar ao TC-C02: material inexistente retorna []
    def test_retorna_lista_vazia_para_material_inexistente(self):
        resultado = get_lead_time_por_material(99999)
        assert resultado == []

    # Complementar ao TC-C02: compras sem lead_time são excluídas
    def test_exclui_compras_sem_lead_time(self):
        material = baker.make("api.DimMaterial")
        fornecedor = baker.make("api.DimFornecedor")
        tempo = baker.make("api.DimTempo")
        status = baker.make(
            "api.DimStatusPedido", nome_status="Aberto", categoria="Pendente"
        )
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=None,
        )
        resultado = get_lead_time_por_material(material.id)
        assert resultado == []

    # TC-C02 — Contrato: fornecedor, lead_time, valor_unidade, valor_total,
    # status, categoria_status e data_pedido
    def test_retorna_campos_corretos(self):
        material = baker.make("api.DimMaterial")
        self._criar_compra(
            material,
            fornecedor_nome="Fornecedor X",
            lead_time=20,
            valor_total=500.0,
            quantidade=5,
        )
        resultado = get_lead_time_por_material(material.id)
        assert len(resultado) == 1
        ponto = resultado[0]
        assert ponto["fornecedor"] == "Fornecedor X"
        assert ponto["lead_time"] == 20
        assert ponto["valor_total"] == approx(500.0)
        assert ponto["status"] == "Entregue"
        assert ponto["categoria_status"] == "Concluído"
        assert ponto["data_pedido"] == "2024-01-01"

    # TC-C02 — Contrato: valor_unidade (number) calculado
    def test_calcula_valor_unidade_corretamente(self):
        material = baker.make("api.DimMaterial")
        self._criar_compra(material, valor_total=1000.0, quantidade=4)
        resultado = get_lead_time_por_material(material.id)
        assert resultado[0]["valor_unidade"] == approx(250.0)

    # Complementar ao TC-C02: proteção contra divisão por zero no valor_unidade
    def test_quantidade_zero_usa_1_para_evitar_divisao_por_zero(self):
        material = baker.make("api.DimMaterial")
        fornecedor = baker.make("api.DimFornecedor", razao_social="F")
        status = baker.make(
            "api.DimStatusPedido", nome_status="Aberto", categoria="Pendente"
        )
        tempo = baker.make(
            "api.DimTempo",
            id=20240301,
            data="2024-03-01",
            ano=2024,
            mes=3,
            trimestre=1,
            semestre=1,
            dia_semana=4,
        )
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=10,
            valor_total=300.0,
            quantidade_solicitada=0,
        )
        resultado = get_lead_time_por_material(material.id)
        assert resultado[0]["valor_unidade"] == approx(300.0)

    # Complementar ao TC-C02: deduplicação do mesmo pedido em projetos diferentes
    def test_deduplica_compras_de_mesmo_pedido_em_projetos_diferentes(self):
        material = baker.make("api.DimMaterial")
        fornecedor = baker.make("api.DimFornecedor", razao_social="Dup Ltda")
        status = baker.make(
            "api.DimStatusPedido", nome_status="Aberto", categoria="Pendente"
        )
        tempo = baker.make(
            "api.DimTempo",
            id=20241208,
            data="2024-12-08",
            ano=2024,
            mes=12,
            trimestre=4,
            semestre=2,
            dia_semana=6,
        )
        projeto1 = baker.make("api.DimProjeto")
        projeto2 = baker.make("api.DimProjeto")
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=25,
            valor_total=1000.0,
            quantidade_solicitada=10,
            projeto=projeto1,
        )
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo,
            status=status,
            lead_time=25,
            valor_total=1000.0,
            quantidade_solicitada=10,
            projeto=projeto2,
        )
        resultado = get_lead_time_por_material(material.id)
        assert len(resultado) == 1

    # Complementar ao TC-C02: compras distintas não são deduplicadas
    def test_nao_deduplica_compras_diferentes(self):
        material = baker.make("api.DimMaterial")
        fornecedor = baker.make("api.DimFornecedor", razao_social="F1")
        status = baker.make(
            "api.DimStatusPedido", nome_status="Aberto", categoria="Pendente"
        )
        tempo1 = baker.make(
            "api.DimTempo",
            id=20240101,
            data="2024-01-01",
            ano=2024,
            mes=1,
            trimestre=1,
            semestre=1,
            dia_semana=0,
        )
        tempo2 = baker.make(
            "api.DimTempo",
            id=20240201,
            data="2024-02-01",
            ano=2024,
            mes=2,
            trimestre=1,
            semestre=1,
            dia_semana=3,
        )
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo1,
            status=status,
            lead_time=10,
            valor_total=500.0,
            quantidade_solicitada=5,
        )
        baker.make(
            "api.FatoCompras",
            material=material,
            fornecedor=fornecedor,
            tempo=tempo2,
            status=status,
            lead_time=20,
            valor_total=800.0,
            quantidade_solicitada=8,
        )
        resultado = get_lead_time_por_material(material.id)
        assert len(resultado) == 2

    # Complementar ao TC-C02: compras de outro material não vazam
    def test_nao_retorna_dados_de_outro_material(self):
        mat1 = baker.make("api.DimMaterial")
        mat2 = baker.make("api.DimMaterial")
        self._criar_compra(mat2, tempo_id=20240501, data="2024-05-01")
        resultado = get_lead_time_por_material(mat1.id)
        assert resultado == []
