import pytest
from pytest import approx
from model_bakery import baker
from api.services.programa_svc import get_horas_por_projeto


@pytest.mark.django_db
class TestGetHorasPorProjeto:

    def _make_tempo(self):
        return baker.make(
            'api.DimTempo',
            id=20230201,
            data='2023-02-01',
            ano=2023,
            mes=2,
            trimestre=1,
            semestre=1,
            dia_semana=2,
        )

    def test_levanta_404_para_programa_inexistente(self):
        from django.http import Http404
        with pytest.raises(Http404):
            get_horas_por_projeto(99999)

    def test_retorna_lista_vazia_quando_programa_sem_projetos(self):
        programa = baker.make('api.DimPrograma')
        resultado = get_horas_por_projeto(programa.id)
        assert resultado == []

    def test_retorna_projeto_com_horas_zero_quando_sem_fato_horas(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', programa=programa, nome_projeto='Projeto A')
        resultado = get_horas_por_projeto(programa.id)
        assert len(resultado) == 1
        assert resultado[0]['nome_projeto'] == 'Projeto A'
        assert resultado[0]['horas_realizadas'] == approx(0.0)

    def test_retorna_horas_realizadas_corretas(self):
        programa = baker.make('api.DimPrograma')
        projeto = baker.make('api.DimProjeto', programa=programa, nome_projeto='Projeto B')
        tempo = self._make_tempo()
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=5.0, custo_horas=0)
        baker.make('api.FatoHoras', projeto=projeto, programa=programa, tempo=tempo, horas_trabalhadas=3.0, custo_horas=0)
        resultado = get_horas_por_projeto(programa.id)
        assert len(resultado) == 1
        assert resultado[0]['horas_realizadas'] == approx(8.0)

    def test_nao_inclui_projetos_de_outro_programa(self):
        programa_a = baker.make('api.DimPrograma')
        programa_b = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', programa=programa_a, nome_projeto='Projeto Alpha')
        baker.make('api.DimProjeto', programa=programa_b, nome_projeto='Projeto Beta')
        resultado = get_horas_por_projeto(programa_a.id)
        nomes = [r['nome_projeto'] for r in resultado]
        assert 'Projeto Alpha' in nomes
        assert 'Projeto Beta' not in nomes

    def test_retorna_multiplos_projetos_ordenados_por_nome(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', programa=programa, nome_projeto='Zebra')
        baker.make('api.DimProjeto', programa=programa, nome_projeto='Alpha')
        baker.make('api.DimProjeto', programa=programa, nome_projeto='Mango')
        resultado = get_horas_por_projeto(programa.id)
        nomes = [r['nome_projeto'] for r in resultado]
        assert nomes == sorted(nomes)

    def test_retorna_campos_corretos(self):
        programa = baker.make('api.DimPrograma')
        baker.make('api.DimProjeto', programa=programa, nome_projeto='Projeto C')
        resultado = get_horas_por_projeto(programa.id)
        assert 'nome_projeto' in resultado[0]
        assert 'horas_realizadas' in resultado[0]

    def test_nao_soma_horas_de_outro_projeto(self):
        programa = baker.make('api.DimPrograma')
        projeto_a = baker.make('api.DimProjeto', programa=programa, nome_projeto='Alfa')
        projeto_b = baker.make('api.DimProjeto', programa=programa, nome_projeto='Beta')
        tempo = self._make_tempo()
        baker.make('api.FatoHoras', projeto=projeto_a, programa=programa, tempo=tempo, horas_trabalhadas=10.0, custo_horas=0)
        baker.make('api.FatoHoras', projeto=projeto_b, programa=programa, tempo=tempo, horas_trabalhadas=4.0, custo_horas=0)
        resultado = get_horas_por_projeto(programa.id)
        por_nome = {r['nome_projeto']: r['horas_realizadas'] for r in resultado}
        assert por_nome['Alfa'] == approx(10.0)
        assert por_nome['Beta'] == approx(4.0)

    def test_projeto_sem_horas_tem_valor_zero_quando_outros_tem_horas(self):
        programa = baker.make('api.DimPrograma')
        projeto_com_horas = baker.make('api.DimProjeto', programa=programa, nome_projeto='Com Horas')
        baker.make('api.DimProjeto', programa=programa, nome_projeto='Sem Horas')
        tempo = self._make_tempo()
        baker.make('api.FatoHoras', projeto=projeto_com_horas, programa=programa, tempo=tempo, horas_trabalhadas=6.0, custo_horas=0)
        resultado = get_horas_por_projeto(programa.id)
        por_nome = {r['nome_projeto']: r['horas_realizadas'] for r in resultado}
        assert por_nome['Com Horas'] == approx(6.0)
        assert por_nome['Sem Horas'] == approx(0.0)
