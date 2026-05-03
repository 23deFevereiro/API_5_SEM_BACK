from api.utils.pagination import normalizar_pagina, calcular_paginacao
from api.services.projeto_svc import formatar_material
from pytest import approx


class TestNormalizarPagina:

    def test_valor_zero_retorna_1(self):
        assert normalizar_pagina(0) == 1

    def test_valor_negativo_retorna_1(self):
        assert normalizar_pagina(-5) == 1

    def test_valor_um_retorna_1(self):
        assert normalizar_pagina(1) == 1

    def test_valor_valido_retorna_o_proprio(self):
        assert normalizar_pagina(3) == 3


class TestCalcularPaginacao:

    def test_primeira_pagina_com_15_itens(self):
        total_pages, start, end = calcular_paginacao(15, 1, 10)
        assert total_pages == 2
        assert start == 0
        assert end == 10

    def test_segunda_pagina_com_15_itens(self):
        total_pages, start, end = calcular_paginacao(15, 2, 10)
        assert total_pages == 2
        assert start == 10
        assert end == 20

    def test_zero_itens_retorna_uma_pagina(self):
        total_pages, _, _ = calcular_paginacao(0, 1, 10)
        assert total_pages == 1

    def test_itens_exatos_sem_resto(self):
        total_pages, _, _ = calcular_paginacao(20, 1, 10)
        assert total_pages == 2

    def test_itens_com_resto_arredonda_para_cima(self):
        total_pages, _, _ = calcular_paginacao(21, 1, 10)
        assert total_pages == 3


class TestFormatarMaterial:

    def test_renomeia_descricao_para_nome_material(self):
        item = {
            'material_id': 1,
            'material__descricao': 'Capacitor',
            'material__custo_estimado': 15.0,
            'quantidade': 5,
            'custo_total_estimado': 75.0,
        }
        resultado = formatar_material(item)
        assert resultado['nome_material'] == 'Capacitor'

    def test_custo_total_nulo_vira_zero(self):
        item = {
            'material_id': 1,
            'material__descricao': 'Resistor',
            'material__custo_estimado': 10.0,
            'quantidade': 3,
            'custo_total_estimado': None,
        }
        resultado = formatar_material(item)
        assert resultado['custo_total_estimado'] == approx(0.0)

    def test_remove_campos_internos_do_orm(self):
        item = {
            'material_id': 1,
            'material__descricao': 'Diodo',
            'material__custo_estimado': 5.0,
            'quantidade': 2,
            'custo_total_estimado': 10.0,
        }
        resultado = formatar_material(item)
        assert 'material_id' not in resultado
        assert 'material__custo_estimado' not in resultado
        assert 'material__descricao' not in resultado

    def test_retorna_quantidade_correta(self):
        item = {
            'material_id': 1,
            'material__descricao': 'Transistor',
            'material__custo_estimado': 8.0,
            'quantidade': 10,
            'custo_total_estimado': 80.0,
        }
        resultado = formatar_material(item)
        assert resultado['quantidade'] == 10

    def test_custo_total_retornado_como_float(self):
        item = {
            'material_id': 1,
            'material__descricao': 'LED',
            'material__custo_estimado': 2.5,
            'quantidade': 4,
            'custo_total_estimado': 10,
        }
        resultado = formatar_material(item)
        assert isinstance(resultado['custo_total_estimado'], float)


class TestParseData:
    def test_retorna_none_quando_valor_nulo(self):
        from api.views.view_utils import _parse_data
        assert _parse_data(None, 'data_inicio') is None

    def test_retorna_none_quando_valor_vazio(self):
        from api.views.view_utils import _parse_data
        assert _parse_data('', 'data_inicio') is None

    def test_retorna_date_quando_valor_valido(self):
        import pytest
        from datetime import date
        from api.views.view_utils import _parse_data
        resultado = _parse_data('2025-01-15', 'data_inicio')
        assert resultado == date(2025, 1, 15)

    def test_levanta_value_error_quando_formato_invalido(self):
        import pytest
        from api.views.view_utils import _parse_data
        with pytest.raises(ValueError, match="data_inicio"):
            _parse_data('15/01/2025', 'data_inicio')
