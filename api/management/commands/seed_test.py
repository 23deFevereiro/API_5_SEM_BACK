"""
Seed de Testes — FATEC API 5 Semestre
======================================
Management command que popula o banco com dados mínimos, controlados
e reproduzíveis para execução dos testes de integração (caixa preta).

Uso:
    python manage.py seed_test

Ou via conftest.py (automático antes da sessão de testes):
    from django.core.management import call_command

    @pytest.fixture(scope="session", autouse=True)
    def seed_database(django_db_setup):
        call_command("seed_test")

O que é criado:
    - 3 programas (2 com projetos, 1 vazio — cobre cenário distribuicao-status vazio)
    - 13 projetos com status variados (12 com horas, 1 sem horas — cobre resumo zerado)
    - 3 funcionários
    - 16 materiais (15 com estoque, 1 sem compras — cobre lead-time vazio)
    - 2 fornecedores
    - Registros de horas em 3 datas distintas
    - Compras com lead times diferentes
    - Registros de estoque (abaixo e acima do mínimo)
    - Status de pedido (Aberto, Entregue, Cancelado)
    - Datas de 2024-01-01 a 2026-06-30
"""

from datetime import date

from django.core.management.base import BaseCommand

from api.models import (
    DimFornecedor,
    DimFuncionario,
    DimMaterial,
    DimPrograma,
    DimProjeto,
    DimStatusPedido,
    DimTarefa,
    DimTempo,
    FatoCompras,
    FatoEstoque,
    FatoHoras,
    FatoMateriais,
)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

ANA_LIMA = "Ana Lima"
CARLOS_MELO = "Carlos Melo"
FERNANDA_CRUZ = "Fernanda Cruz"
RICARDO_NEVES = "Ricardo Neves"

STATUS_PLANEJAMENTO = "Planejamento"
STATUS_EM_ANDAMENTO = "Em andamento"
STATUS_CONCLUIDO = "Concluído"
STATUS_SUSPENSO = "Suspenso"
STATUS_TAREFA_CONCLUIDA = "Concluída"

CATEGORIA_ELETRONICO = "Eletrônico"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tempo(data: date) -> DimTempo:
    """Cria ou retorna um DimTempo para a data informada."""
    tempo_id = int(data.strftime("%Y%m%d"))
    obj, _ = DimTempo.objects.get_or_create(
        id=tempo_id,
        defaults={
            "data": data,
            "ano": data.year,
            "mes": data.month,
            "trimestre": (data.month - 1) // 3 + 1,
            "semestre": 1 if data.month <= 6 else 2,
            "dia_semana": data.weekday(),
        },
    )
    return obj


# ---------------------------------------------------------------------------
# Criação das entidades
# ---------------------------------------------------------------------------


def criar_programas():
    """
    3 programas:
    - PGM-001 e PGM-002: com projetos e dados — cobrem cenários happy path
    - PGM-003: sem projetos
      — cobre cenário distribuicao-status vazio (total=0, status=[])
    Necessário para:
    TC-PR01, TC-PR02, TC-PR03, TC-PR04, TC-PR05, TC-PR09
    """
    programa_norte = DimPrograma.objects.create(
        id=1,
        codigo_programa="PGM-001",
        nome_programa="Programa Norte",
        gerente_programa=ANA_LIMA,
        data_inicio=date(2024, 1, 1),
        data_fim_prevista=date(2026, 12, 31),
        status=STATUS_EM_ANDAMENTO,
    )
    programa_sul = DimPrograma.objects.create(
        id=2,
        codigo_programa="PGM-002",
        nome_programa="Programa Sul",
        gerente_programa=CARLOS_MELO,
        data_inicio=date(2024, 3, 1),
        data_fim_prevista=date(2026, 6, 30),
        status=STATUS_EM_ANDAMENTO,
    )
    # Programa vazio — sem projetos vinculados
    # Cobre: GET /programas/{id}/distribuicao-status/ -> {"total": 0, "status": []}
    # Cobre: GET /programas/{id}/resumo/ -> todos os campos zerados
    # Cobre: GET /programas/{id}/horas-por-projeto/ -> []
    # Cobre: GET /programas/{id}/tabela-projetos/ -> count=0, results=[]
    DimPrograma.objects.create(
        id=3,
        codigo_programa="PGM-003",
        nome_programa="Programa Vazio",
        gerente_programa=RICARDO_NEVES,
        data_inicio=date(2025, 1, 1),
        data_fim_prevista=date(2026, 12, 31),
        status=STATUS_PLANEJAMENTO,
    )
    print("   ✅ programas: 3 registros (2 com projetos, 1 vazio)")
    return programa_norte, programa_sul


def criar_projetos(programa_norte, programa_sul):
    """
    12 projetos distribuídos entre os dois programas com status variados.
    Necessário para: TC-P01, TC-P03, TC-PR03, TC-PR06, TC-PR11
    Status cobertos: Planejamento, Em andamento, Suspenso, Concluído
    """

    prazo_futuro = date(2026, 12, 31)
    prazo_passado = date(2024, 6, 30)

    projetos_norte = [
        DimProjeto.objects.create(
            id=1,
            codigo_projeto="PRJ-001",
            nome_projeto="Sistema de Telemetria",
            programa=programa_norte,
            responsavel=ANA_LIMA,
            custo_hora=150.0,
            status=STATUS_EM_ANDAMENTO,
            data_inicio=date(2024, 1, 1),
            data_fim_prevista=prazo_futuro,
        ),
        DimProjeto.objects.create(
            id=2,
            codigo_projeto="PRJ-002",
            nome_projeto="Módulo de Navegação GPS",
            programa=programa_norte,
            responsavel=CARLOS_MELO,
            custo_hora=120.0,
            status=STATUS_EM_ANDAMENTO,
            data_inicio=date(2024, 2, 1),
            data_fim_prevista=prazo_passado,
        ),
        DimProjeto.objects.create(
            id=3,
            codigo_projeto="PRJ-003",
            nome_projeto="Central de Comunicação",
            programa=programa_norte,
            responsavel=ANA_LIMA,
            custo_hora=130.0,
            status=STATUS_CONCLUIDO,
            data_inicio=date(2024, 1, 1),
            data_fim_prevista=date(2024, 12, 31),
        ),
        DimProjeto.objects.create(
            id=4,
            codigo_projeto="PRJ-004",
            nome_projeto="Plataforma de Simulação",
            programa=programa_norte,
            responsavel=FERNANDA_CRUZ,
            custo_hora=140.0,
            status=STATUS_SUSPENSO,
            data_inicio=date(2024, 3, 1),
            data_fim_prevista=prazo_futuro,
        ),
        DimProjeto.objects.create(
            id=5,
            codigo_projeto="PRJ-005",
            nome_projeto="Sistema de Propulsão",
            programa=programa_norte,
            responsavel=CARLOS_MELO,
            custo_hora=160.0,
            status=STATUS_PLANEJAMENTO,
            data_inicio=date(2025, 1, 1),
            data_fim_prevista=prazo_futuro,
        ),
        DimProjeto.objects.create(
            id=6,
            codigo_projeto="PRJ-006",
            nome_projeto="Controle de Atitude",
            programa=programa_norte,
            responsavel=ANA_LIMA,
            custo_hora=150.0,
            status=STATUS_CONCLUIDO,
            data_inicio=date(2024, 1, 1),
            data_fim_prevista=date(2025, 6, 30),
        ),
    ]

    projetos_sul = [
        DimProjeto.objects.create(
            id=7,
            codigo_projeto="PRJ-007",
            nome_projeto="Integração de Subsistemas",
            programa=programa_sul,
            responsavel=RICARDO_NEVES,
            custo_hora=145.0,
            status=STATUS_EM_ANDAMENTO,
            data_inicio=date(2024, 4, 1),
            data_fim_prevista=prazo_futuro,
        ),
        DimProjeto.objects.create(
            id=8,
            codigo_projeto="PRJ-008",
            nome_projeto="Módulo de Energia Solar",
            programa=programa_sul,
            responsavel=FERNANDA_CRUZ,
            custo_hora=135.0,
            status=STATUS_EM_ANDAMENTO,
            data_inicio=date(2024, 5, 1),
            data_fim_prevista=prazo_passado,
        ),
        DimProjeto.objects.create(
            id=9,
            codigo_projeto="PRJ-009",
            nome_projeto="Sistema de Arrefecimento",
            programa=programa_sul,
            responsavel=RICARDO_NEVES,
            custo_hora=125.0,
            status=STATUS_CONCLUIDO,
            data_inicio=date(2024, 1, 1),
            data_fim_prevista=date(2024, 12, 31),
        ),
        DimProjeto.objects.create(
            id=10,
            codigo_projeto="PRJ-010",
            nome_projeto="Banco de Dados Embarcado",
            programa=programa_sul,
            responsavel=FERNANDA_CRUZ,
            custo_hora=155.0,
            status=STATUS_SUSPENSO,
            data_inicio=date(2024, 6, 1),
            data_fim_prevista=prazo_futuro,
        ),
        DimProjeto.objects.create(
            id=11,
            codigo_projeto="PRJ-011",
            nome_projeto="Interface de Controle",
            programa=programa_sul,
            responsavel=RICARDO_NEVES,
            custo_hora=140.0,
            status=STATUS_PLANEJAMENTO,
            data_inicio=date(2025, 2, 1),
            data_fim_prevista=prazo_futuro,
        ),
        DimProjeto.objects.create(
            id=12,
            codigo_projeto="PRJ-012",
            nome_projeto="Módulo de Telemetria II",
            programa=programa_sul,
            responsavel=FERNANDA_CRUZ,
            custo_hora=150.0,
            status=STATUS_CONCLUIDO,
            data_inicio=date(2024, 1, 1),
            data_fim_prevista=date(2025, 3, 31),
        ),
    ]

    # Projeto sem horas — cobre cenários de zeros e lista vazia
    # Cobre: GET /projetos/{id}/resumo/ -> custo_total=0, tempo_total=0
    # Cobre: GET /projetos/{id}/horas-por-funcionario/ -> []
    # Cobre: GET /projetos/{id}/funcionarios/ -> count=0, results=[]
    # Cobre: tabela-projetos -> sem_horas_registradas=True, data_ultima_atividade=null
    projeto_sem_horas = DimProjeto.objects.create(
        id=13,
        codigo_projeto="PRJ-013",
        nome_projeto="Projeto Sem Horas",
        programa=programa_norte,
        responsavel=ANA_LIMA,
        custo_hora=100.0,
        status=STATUS_EM_ANDAMENTO,
        data_inicio=date(2025, 1, 1),
        data_fim_prevista=prazo_futuro,
    )
    projetos_norte.append(projeto_sem_horas)

    print("   ✅ projetos: 13 registros (12 com horas, 1 sem horas)")
    return projetos_norte, projetos_sul


def criar_funcionarios():
    """
    3 funcionários alocados a projetos diferentes.
    Necessário para: TC-P05, TC-P06
    """
    funcionarios = [
        DimFuncionario.objects.create(nome=ANA_LIMA),
        DimFuncionario.objects.create(nome=CARLOS_MELO),
        DimFuncionario.objects.create(nome=FERNANDA_CRUZ),
    ]
    print("   ✅ funcionarios: 3 registros")
    return funcionarios


def criar_tarefas(projetos_norte, projetos_sul):
    """
    Tarefas para os projetos — necessárias para cálculo de horas estimadas
    e desvio no TC-PR06.
    """
    tarefas = []
    todos_projetos = projetos_norte + projetos_sul
    tarefa_id = 1
    for projeto in todos_projetos:
        tarefas.append(
            DimTarefa.objects.create(
                id=tarefa_id,
                codigo_tarefa=f"TSK-{projeto.codigo_projeto}-001",
                projeto=projeto,
                titulo=f"Tarefa 1 - {projeto.nome_projeto}",
                responsavel=projeto.responsavel,
                horas_estimadas=40.0,
                status=STATUS_TAREFA_CONCLUIDA,
            )
        )
        tarefa_id += 1
        tarefas.append(
            DimTarefa.objects.create(
                id=tarefa_id,
                codigo_tarefa=f"TSK-{projeto.codigo_projeto}-002",
                projeto=projeto,
                titulo=f"Tarefa 2 - {projeto.nome_projeto}",
                responsavel=projeto.responsavel,
                horas_estimadas=20.0,
                status=STATUS_EM_ANDAMENTO,
            )
        )
        tarefa_id += 1
    print(f"   ✅ tarefas: {len(tarefas)} registros")
    return tarefas


def criar_materiais():
    """
    15 materiais com estoques variados (crítico, atenção e ok).
    Necessário para: TC-C03, TC-C04, TC-P04, TC-P05
    """
    materiais = [
        # Materiais críticos (dias_cobertura <= 30)
        DimMaterial.objects.create(
            id=1,
            codigo_material="MAT-001",
            descricao="Capacitor Cerâmico 1nF 0402",
            categoria=CATEGORIA_ELETRONICO,
            fabricante="VoltParts",
            custo_estimado=1.50,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=2,
            codigo_material="MAT-002",
            descricao="Resistor SMD 100R 0402",
            categoria=CATEGORIA_ELETRONICO,
            fabricante="ResistorCo",
            custo_estimado=0.80,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=3,
            codigo_material="MAT-003",
            descricao="Transistor NPN 2N2222",
            categoria=CATEGORIA_ELETRONICO,
            fabricante="SemiCo",
            custo_estimado=2.50,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=4,
            codigo_material="MAT-004",
            descricao="LED Infravermelho 940nm",
            categoria=CATEGORIA_ELETRONICO,
            fabricante="LedTech",
            custo_estimado=1.20,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=5,
            codigo_material="MAT-005",
            descricao="Sensor Umidade DHT22",
            categoria="Sensor",
            fabricante="SensorPro",
            custo_estimado=15.00,
            status="Ativo",
        ),
        # Materiais em atenção (dias_cobertura entre 31 e 60)
        DimMaterial.objects.create(
            id=6,
            codigo_material="MAT-006",
            descricao="Microcontrolador STM32F103",
            categoria=CATEGORIA_ELETRONICO,
            fabricante="STMicro",
            custo_estimado=45.90,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=7,
            codigo_material="MAT-007",
            descricao="Módulo GPS NEO-M8N",
            categoria="Comunicação",
            fabricante="uBlox",
            custo_estimado=128.50,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=8,
            codigo_material="MAT-008",
            descricao="Display OLED 0.96 polegadas",
            categoria="Display",
            fabricante="DisplayTech",
            custo_estimado=22.90,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=9,
            codigo_material="MAT-009",
            descricao="Módulo RF LoRa SX1276",
            categoria="Comunicação",
            fabricante="Semtech",
            custo_estimado=95.00,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=10,
            codigo_material="MAT-010",
            descricao="Bateria LiPo 5000mAh",
            categoria="Energia",
            fabricante="PowerCell",
            custo_estimado=210.00,
            status="Ativo",
        ),
        # Materiais ok (dias_cobertura > 60)
        DimMaterial.objects.create(
            id=11,
            codigo_material="MAT-011",
            descricao="Regulador de Tensão LM7805",
            categoria=CATEGORIA_ELETRONICO,
            fabricante="TI",
            custo_estimado=4.20,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=12,
            codigo_material="MAT-012",
            descricao="Osciloscópio Portátil",
            categoria="Instrumento",
            fabricante="Rigol",
            custo_estimado=1250.00,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=13,
            codigo_material="MAT-013",
            descricao="Motor Brushless 2208",
            categoria="Mecânico",
            fabricante="MotorTech",
            custo_estimado=89.00,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=14,
            codigo_material="MAT-014",
            descricao="FPGA Xilinx Artix-7",
            categoria=CATEGORIA_ELETRONICO,
            fabricante="Xilinx",
            custo_estimado=780.00,
            status="Ativo",
        ),
        DimMaterial.objects.create(
            id=15,
            codigo_material="MAT-015",
            descricao="Fonte Chaveada 12V 5A",
            categoria="Energia",
            fabricante="MeanWell",
            custo_estimado=145.00,
            status="Ativo",
        ),
    ]
    # Material sem compras — cobre cenário lead-time vazio
    # Cobre: GET /compras/lead-time/?material_id={id} -> []
    materiais.append(
        DimMaterial.objects.create(
            id=16,
            codigo_material="MAT-016",
            descricao="Material Sem Compras",
            categoria=CATEGORIA_ELETRONICO,
            fabricante="TestFab",
            custo_estimado=10.00,
            status="Ativo",
        )
    )
    print("   ✅ materiais: 16 registros (15 com estoque, 1 sem compras)")
    return materiais


def criar_fornecedores():
    """
    2 fornecedores com lead times diferentes.
    Necessário para: TC-C02, TC-C03
    """
    fornecedores = [
        DimFornecedor.objects.create(
            id=1,
            codigo_fornecedor="FOR-001",
            razao_social="VoltParts 64 Ltda",
            cidade="São Paulo",
            estado="SP",
            categoria=CATEGORIA_ELETRONICO,
            status="Ativo",
        ),
        DimFornecedor.objects.create(
            id=2,
            codigo_fornecedor="FOR-002",
            razao_social="TechSupply Brasil",
            cidade="Campinas",
            estado="SP",
            categoria="Geral",
            status="Ativo",
        ),
    ]
    print("   ✅ fornecedores: 2 registros")
    return fornecedores


def criar_status_pedido():
    """
    Status de pedido necessários para compras e alertas.
    Necessário para: TC-C02, TC-C03, TC-C04
    """
    status_list = [
        DimStatusPedido.objects.create(
            nome_status="Aberto",
            categoria="Pendente",
            ordem_prioridade=1,
        ),
        DimStatusPedido.objects.create(
            nome_status="Entregue",
            categoria=STATUS_CONCLUIDO,
            ordem_prioridade=2,
        ),
        DimStatusPedido.objects.create(
            nome_status="Cancelado",
            categoria="Cancelado",
            ordem_prioridade=3,
        ),
    ]
    print("   ✅ status_pedido: 3 registros")
    return status_list


def criar_fato_horas(projetos_norte, projetos_sul, funcionarios, programas):
    """
    Registros de horas em 3 datas distintas para burnup e séries temporais.
    Necessário para: TC-P05, TC-P07, TC-PR04, TC-PR07
    """
    programa_norte, programa_sul = programas
    ana, carlos, fernanda = funcionarios

    datas = [
        date(2025, 1, 15),
        date(2025, 6, 15),
        date(2026, 1, 15),
    ]
    tempos = [_make_tempo(d) for d in datas]

    registros = 0

    # Horas nos projetos do Programa Norte
    projeto_principal = projetos_norte[0]  # PRJ-001
    tarefa = DimTarefa.objects.filter(projeto=projeto_principal).first()

    for tempo in tempos:
        FatoHoras.objects.create(
            tempo=tempo,
            projeto=projeto_principal,
            programa=programa_norte,
            funcionario=ana,
            tarefa=tarefa,
            horas_trabalhadas=40.0,
            custo_horas=6000.0,
        )
        FatoHoras.objects.create(
            tempo=tempo,
            projeto=projeto_principal,
            programa=programa_norte,
            funcionario=carlos,
            tarefa=tarefa,
            horas_trabalhadas=20.0,
            custo_horas=2400.0,
        )
        registros += 2

    # Horas nos projetos do Programa Sul
    projeto_sul = projetos_sul[0]  # PRJ-007
    tarefa_sul = DimTarefa.objects.filter(projeto=projeto_sul).first()

    for tempo in tempos:
        FatoHoras.objects.create(
            tempo=tempo,
            projeto=projeto_sul,
            programa=programa_sul,
            funcionario=fernanda,
            tarefa=tarefa_sul,
            horas_trabalhadas=30.0,
            custo_horas=4350.0,
        )
        registros += 1

    print(f"   ✅ fato_horas: {registros} registros")


def criar_fato_materiais(
    projetos_norte, projetos_sul, materiais, fornecedores, programas
):
    """
    Empenhos de materiais por projeto.
    Necessário para: TC-P04, TC-P05, TC-C04
    """
    programa_norte, programa_sul = programas
    fornecedor_a, fornecedor_b = fornecedores

    datas = [date(2025, 1, 15), date(2025, 6, 15), date(2026, 1, 15)]
    tempos = [_make_tempo(d) for d in datas]

    registros = 0
    projeto_norte = projetos_norte[0]
    projeto_sul = projetos_sul[0]

    for i, material in enumerate(materiais[:10]):
        tempo = tempos[i % 3]
        fornecedor = fornecedor_a if i % 2 == 0 else fornecedor_b
        quantidade = (i + 1) * 5

        FatoMateriais.objects.create(
            tempo=tempo,
            projeto=projeto_norte,
            programa=programa_norte,
            material=material,
            fornecedor=fornecedor,
            quantidade_empenhada=quantidade,
            custo_materiais=float(quantidade) * float(material.custo_estimado),
        )
        registros += 1

    for i, material in enumerate(materiais[10:]):
        tempo = tempos[i % 3]
        quantidade = (i + 1) * 3

        FatoMateriais.objects.create(
            tempo=tempo,
            projeto=projeto_sul,
            programa=programa_sul,
            material=material,
            fornecedor=fornecedor_b,
            quantidade_empenhada=quantidade,
            custo_materiais=float(quantidade) * float(material.custo_estimado),
        )
        registros += 1

    print(f"   ✅ fato_materiais: {registros} registros")


def criar_fato_compras(materiais, fornecedores, projetos_norte, status_list):
    """
    Compras com lead times diferentes e status variados.
    Necessário para: TC-C01, TC-C02, TC-C03
    Cobre: compra entregue, aberta e cancelada
    """
    fornecedor_a, fornecedor_b = fornecedores
    status_aberto = next(s for s in status_list if s.nome_status == "Aberto")
    status_entregue = next(s for s in status_list if s.nome_status == "Entregue")
    status_cancelado = next(s for s in status_list if s.nome_status == "Cancelado")

    tempo_compra = _make_tempo(date(2025, 1, 15))
    projeto = projetos_norte[0]

    registros = 0

    # Material crítico — lead_time alto, estoque baixo
    material_critico = materiais[0]
    FatoCompras.objects.create(
        tempo=tempo_compra,
        projeto=projeto,
        material=material_critico,
        fornecedor=fornecedor_a,
        status=status_entregue,
        quantidade_solicitada=100,
        quantidade_entregue=100,
        valor_alocado=150.0,
        valor_total=150.0,
        lead_time=28,
        data_previsao_entrega=date(2025, 2, 12),
    )
    registros += 1

    # Material em atenção — lead_time médio
    material_atencao = materiais[5]
    FatoCompras.objects.create(
        tempo=tempo_compra,
        projeto=projeto,
        material=material_atencao,
        fornecedor=fornecedor_b,
        status=status_aberto,
        quantidade_solicitada=50,
        quantidade_entregue=0,
        valor_alocado=2295.0,
        valor_total=2295.0,
        lead_time=15,
        data_previsao_entrega=date(2025, 1, 30),
    )
    registros += 1

    # Compra cancelada — não deve entrar no custo_real
    material_ok = materiais[10]
    FatoCompras.objects.create(
        tempo=tempo_compra,
        projeto=projeto,
        material=material_ok,
        fornecedor=fornecedor_a,
        status=status_cancelado,
        quantidade_solicitada=20,
        quantidade_entregue=0,
        valor_alocado=84.0,
        valor_total=84.0,
        lead_time=10,
        data_previsao_entrega=date(2025, 1, 25),
    )
    registros += 1

    print(f"   ✅ fato_compras: {registros} registros")


def criar_fato_estoque(materiais, projetos_norte, projetos_sul):
    """
    Estoques variados para cobrir cenários crítico, atenção e ok.
    Necessário para: TC-C03, TC-C04

    Boundary test incluído:
    - MAT-001: estoque=0  → Urgente (dias_ate_acabar <= critico_max=30)
    - MAT-006: estoque=50 → Atenção (entre 30 e 60)
    - MAT-011: estoque=200 → Ok (> atencao_max=60)
    - MAT-003: estoque=30 → boundary exato no critico_max=30 → Urgente
    """
    tempo = _make_tempo(date(2026, 1, 15))
    projeto_norte = projetos_norte[0]
    projeto_sul = projetos_sul[0]

    estoques = [
        # Críticos (dias_ate_acabar <= 30)
        (materiais[0], projeto_norte, 0),  # MAT-001: zerado → Urgente
        (materiais[1], projeto_norte, 5),  # MAT-002: muito baixo → Urgente
        (materiais[2], projeto_norte, 30),  # MAT-003: boundary exato → Urgente
        (materiais[3], projeto_norte, 10),  # MAT-004: baixo → Urgente
        (materiais[4], projeto_norte, 15),  # MAT-005: baixo → Urgente
        # Atenção (dias_ate_acabar entre 31 e 60)
        (materiais[5], projeto_norte, 50),  # MAT-006: médio → Atenção
        (materiais[6], projeto_sul, 45),  # MAT-007: médio → Atenção
        (materiais[7], projeto_sul, 55),  # MAT-008: médio → Atenção
        (materiais[8], projeto_sul, 40),  # MAT-009: médio → Atenção
        (materiais[9], projeto_sul, 35),  # MAT-010: médio → Atenção
        # Ok (dias_ate_acabar > 60)
        (materiais[10], projeto_norte, 200),  # MAT-011: alto → Ok
        (materiais[11], projeto_norte, 500),  # MAT-012: alto → Ok
        (materiais[12], projeto_sul, 300),  # MAT-013: alto → Ok
        (materiais[13], projeto_sul, 150),  # MAT-014: alto → Ok
        (materiais[14], projeto_sul, 400),  # MAT-015: alto → Ok
    ]

    registros = 0
    for material, projeto, quantidade in estoques:
        FatoEstoque.objects.create(
            tempo=tempo,
            material=material,
            projeto=projeto,
            quantidade_estoque=quantidade,
        )
        registros += 1

    print(f"   ✅ fato_estoque: {registros} registros")


# ---------------------------------------------------------------------------
# Limpeza do banco
# ---------------------------------------------------------------------------


def limpar_banco():
    """
    Remove todos os dados existentes antes de inserir a seed.
    A ordem respeita as dependências entre tabelas (fatos antes de dimensões).
    """
    FatoEstoque.objects.all().delete()
    FatoCompras.objects.all().delete()
    FatoMateriais.objects.all().delete()
    FatoHoras.objects.all().delete()
    DimTarefa.objects.all().delete()
    DimTempo.objects.all().delete()
    DimStatusPedido.objects.all().delete()
    DimFuncionario.objects.all().delete()
    DimFornecedor.objects.all().delete()
    DimMaterial.objects.all().delete()
    DimProjeto.objects.all().delete()
    DimPrograma.objects.all().delete()
    print("   ✅ banco limpo")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run():
    print("\n📦 Seed de Testes — populando banco com dados controlados...\n")

    print("   🗑️  Limpando banco...")
    limpar_banco()

    print("\n   📥 Criando dimensões...")
    programa_norte, programa_sul = criar_programas()
    projetos_norte, projetos_sul = criar_projetos(programa_norte, programa_sul)
    funcionarios = criar_funcionarios()
    criar_tarefas(projetos_norte, projetos_sul)
    materiais = criar_materiais()
    fornecedores = criar_fornecedores()
    status_list = criar_status_pedido()

    print("\n   📊 Criando fatos...")
    programas = (programa_norte, programa_sul)
    criar_fato_horas(projetos_norte, projetos_sul, funcionarios, programas)
    criar_fato_materiais(
        projetos_norte, projetos_sul, materiais, fornecedores, programas
    )
    criar_fato_compras(materiais, fornecedores, projetos_norte, status_list)
    criar_fato_estoque(materiais, projetos_norte, projetos_sul)

    print("\n✅ Seed de testes concluída com sucesso!")
    print("\nResumo:")
    print(f"   Programas:      {DimPrograma.objects.count()} (2 com projetos, 1 vazio)")
    print(
        f"   Projetos:       {DimProjeto.objects.count()} (12 com horas, 1 sem horas)"
    )
    print(f"   Funcionários:   {DimFuncionario.objects.count()}")
    print(
        "   Materiais:      "
        f"{DimMaterial.objects.count()} "
        "(15 com estoque, 1 sem compras)"
    )
    print(f"   Fornecedores:   {DimFornecedor.objects.count()}")
    print(f"   Status pedido:  {DimStatusPedido.objects.count()}")
    print(f"   Tarefas:        {DimTarefa.objects.count()}")
    print(f"   Fato horas:     {FatoHoras.objects.count()}")
    print(f"   Fato materiais: {FatoMateriais.objects.count()}")
    print(f"   Fato compras:   {FatoCompras.objects.count()}")
    print(f"   Fato estoque:   {FatoEstoque.objects.count()}")
    programa_vazio = DimPrograma.objects.get(codigo_programa="PGM-003")
    projeto_sem_horas = DimProjeto.objects.get(codigo_projeto="PRJ-013")
    material_sem_compras = DimMaterial.objects.get(codigo_material="MAT-016")
    print("\nCenários especiais (ids para usar nos testes):")

    print(
        "   Programa vazio:       "
        f"id={programa_vazio.id} "
        f"({programa_vazio.nome_programa})"
    )

    print(
        "   Projeto sem horas:    "
        f"id={projeto_sem_horas.id} "
        f"({projeto_sem_horas.nome_projeto})"
    )

    print(
        "   Material sem compras: "
        f"id={material_sem_compras.id} "
        f"({material_sem_compras.descricao})"
    )


class Command(BaseCommand):
    help = (
        "Seed de testes: popula o banco com dados mínimos "
        "e controlados para testes de integração"
    )

    def handle(self, *args, **options):
        run()
