from api.utils.pagination import normalizar_pagina, calcular_paginacao


class TestNormalizarPaginaFuncionario:

    def test_valor_zero_retorna_1(self):
        assert normalizar_pagina(0) == 1

    def test_valor_negativo_retorna_1(self):
        assert normalizar_pagina(-3) == 1

    def test_valor_valido_retorna_o_proprio(self):
        assert normalizar_pagina(2) == 2


class TestCalcularPaginacaoFuncionario:

    def test_primeira_pagina_com_15_funcionarios(self):
        total_pages, start, end = calcular_paginacao(15, 1, 10)
        assert total_pages == 2
        assert start == 0
        assert end == 10

    def test_segunda_pagina_com_15_funcionarios(self):
        total_pages, start, end = calcular_paginacao(15, 2, 10)
        assert total_pages == 2
        assert start == 10
        assert end == 20

    def test_zero_funcionarios_retorna_uma_pagina(self):
        total_pages, _, _ = calcular_paginacao(0, 1, 10)
        assert total_pages == 1

    def test_funcionarios_exatos_sem_resto(self):
        total_pages, _, _ = calcular_paginacao(20, 1, 10)
        assert total_pages == 2

    def test_funcionarios_com_resto_arredonda_para_cima(self):
        total_pages, _, _ = calcular_paginacao(21, 1, 10)
        assert total_pages == 3

    def test_pagina_maior_que_total(self):
        total_pages, _, _ = calcular_paginacao(15, 5, 10)
        assert total_pages == 2
        