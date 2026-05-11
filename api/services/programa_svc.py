from datetime import date
from decimal import Decimal

from django.db.models import Count, Max, Sum
from django.shortcuts import get_object_or_404

from ..models import (
    DimPrograma,
    DimProjeto,
    DimTarefa,
    FatoCompras,
    FatoHoras,
    FatoMateriais,
)
from ..utils.pagination import calcular_paginacao, normalizar_pagina

STATUS_PLANEJAMENTO = "Planejamento"
STATUS_EM_ANDAMENTO = "Em andamento"
STATUS_SUSPENSO = "Suspenso"
STATUS_CONCLUIDO = "Concluído"

STATUS_PADRAO = [
    STATUS_PLANEJAMENTO,
    STATUS_EM_ANDAMENTO,
    STATUS_SUSPENSO,
    STATUS_CONCLUIDO,
]

STATUS_CORES = {
    STATUS_PLANEJAMENTO: "#3B82F6",
    STATUS_EM_ANDAMENTO: "#EAB308",
    STATUS_SUSPENSO: "#F97316",
    STATUS_CONCLUIDO: "#22C55E",
}


CAMPOS_ORDENACAO_DB = {"nome_projeto", "responsavel", "status"}

ACAO_ORDEM = {
    "priorizar-vermelho": 0,
    "corrigir-status": 1,
    "outro": 2,
    "priorizar-verde": 3,
    "check-vermelho": 4,
    "check-amarelo": 5,
    "check-verde": 6,
    "suspenso": 7,
}


def get_horas_por_projeto(programa_id):
    get_object_or_404(DimPrograma, id=programa_id)

    projetos = DimProjeto.objects.filter(programa_id=programa_id).order_by(
        "nome_projeto"
    )

    horas_por_projeto = (
        FatoHoras.objects.filter(projeto__programa_id=programa_id)
        .values("projeto_id", "projeto__nome_projeto")
        .annotate(horas_realizadas=Sum("horas_trabalhadas"))
    )

    horas_map = {
        row["projeto_id"]: float(row["horas_realizadas"] or 0)
        for row in horas_por_projeto
    }

    return [
        {
            "nome_projeto": projeto.nome_projeto,
            "horas_realizadas": horas_map.get(projeto.id, 0.0),
        }
        for projeto in projetos
    ]


def listar_programas(search=""):
    programas = DimPrograma.objects.all()
    if search:
        programas = programas.filter(nome_programa__icontains=search)
    return list(programas.values("id", "codigo_programa", "nome_programa"))


def get_resumo_programa(programa_id):
    get_object_or_404(DimPrograma, id=programa_id)

    projetos_ids = DimProjeto.objects.filter(programa_id=programa_id).values_list(
        "id", flat=True
    )

    total_projetos = len(projetos_ids)

    horas_estimadas = DimTarefa.objects.filter(projeto_id__in=projetos_ids).aggregate(
        total=Sum("horas_estimadas")
    )["total"] or Decimal("0")

    horas_realizadas = FatoHoras.objects.filter(projeto_id__in=projetos_ids).aggregate(
        total=Sum("horas_trabalhadas")
    )["total"] or Decimal("0")

    custo_estimado_mao_de_obra = FatoHoras.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(total=Sum("custo_horas"))["total"] or Decimal("0")

    custo_estimado_materiais = FatoMateriais.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(total=Sum("custo_materiais"))["total"] or Decimal("0")

    custo_estimado = custo_estimado_mao_de_obra + custo_estimado_materiais

    custo_real_mao_de_obra = FatoHoras.objects.filter(
        projeto_id__in=projetos_ids
    ).aggregate(total=Sum("custo_horas"))["total"] or Decimal("0")

    custo_real_materiais = FatoCompras.objects.filter(
        projeto_id__in=projetos_ids
    ).exclude(status__nome_status="Cancelado").aggregate(total=Sum("valor_alocado"))[
        "total"
    ] or Decimal(
        "0"
    )

    custo_real = custo_real_mao_de_obra + custo_real_materiais

    return {
        "total_projetos": total_projetos,
        "horas_estimadas": horas_estimadas,
        "horas_realizadas": horas_realizadas,
        "custo_estimado": custo_estimado,
        "custo_real": custo_real,
    }


def _calcular_acao_concluido(projeto, tarefas):
    if not projeto.data_fim_prevista:
        return "check-verde"
    tarefas_ids = list(tarefas.values_list("id", flat=True))
    datas_por_tarefa = (
        FatoHoras.objects.filter(tarefa_id__in=tarefas_ids)
        .values("tarefa_id")
        .annotate(ultima_data=Max("tempo__data"))
    )
    tarefas_dentro = sum(
        1
        for t in datas_por_tarefa
        if t["ultima_data"] and t["ultima_data"] <= projeto.data_fim_prevista
    )
    tarefas_fora = sum(
        1
        for t in datas_por_tarefa
        if t["ultima_data"] and t["ultima_data"] > projeto.data_fim_prevista
    )
    if tarefas_fora == 0:
        return "check-verde"
    if tarefas_dentro == 0:
        return "check-vermelho"
    return "check-amarelo"


def _calcular_acao(projeto, total_tarefas, todas_concluidas, dentro_do_prazo, tarefas):
    if projeto.status == STATUS_SUSPENSO:
        return "suspenso"
    if projeto.status == STATUS_CONCLUIDO and total_tarefas == 0:
        return "check-verde"
    if todas_concluidas and projeto.status in (
        STATUS_EM_ANDAMENTO,
        STATUS_PLANEJAMENTO,
    ):
        return "corrigir-status"
    if projeto.status == STATUS_CONCLUIDO and todas_concluidas:
        return _calcular_acao_concluido(projeto, tarefas)
    if projeto.status not in (STATUS_CONCLUIDO, STATUS_SUSPENSO):
        return "priorizar-verde" if dentro_do_prazo else "priorizar-vermelho"
    return "outro"


def _processar_projeto(projeto, hoje):
    tarefas = DimTarefa.objects.filter(projeto=projeto)
    total_tarefas = tarefas.count()
    tarefas_concluidas = tarefas.filter(status="Concluída").count()

    horas_estimadas = tarefas.aggregate(total=Sum("horas_estimadas"))[
        "total"
    ] or Decimal("0")
    horas_realizadas = FatoHoras.objects.filter(projeto=projeto).aggregate(
        total=Sum("horas_trabalhadas")
    )["total"] or Decimal("0")

    desvio = horas_realizadas - horas_estimadas
    percentual_desvio = (
        abs(float(desvio) / float(horas_estimadas)) * 100 if horas_estimadas > 0 else 0
    )
    percentual_tarefas = (
        round((tarefas_concluidas / total_tarefas) * 100, 1) if total_tarefas > 0 else 0
    )

    data_ultima_atividade = FatoHoras.objects.filter(projeto=projeto).aggregate(
        ultima=Max("tempo__data")
    )["ultima"]

    dentro_do_prazo = (
        projeto.data_fim_prevista is None or hoje <= projeto.data_fim_prevista
    )
    todas_concluidas = total_tarefas > 0 and tarefas_concluidas == total_tarefas
    acao = _calcular_acao(
        projeto, total_tarefas, todas_concluidas, dentro_do_prazo, tarefas
    )

    return {
        'nome_projeto': projeto.nome_projeto,
        'responsavel': projeto.responsavel,
        'status': projeto.status,
        'horas_estimadas': float(horas_estimadas),
        'horas_realizadas': float(horas_realizadas),
        'total_tarefas': total_tarefas,
        'tarefas_concluidas': tarefas_concluidas,
        'percentual_tarefas_concluidas': percentual_tarefas,
        'desvio_horas': float(desvio),
        'percentual_desvio': round(percentual_desvio, 1),
        'data_ultima_atividade': data_ultima_atividade.isoformat() if data_ultima_atividade else None,
        'dias_desde_ultima_atividade': (hoje - data_ultima_atividade).days if data_ultima_atividade else None,
        'dentro_do_prazo': dentro_do_prazo,
        'sem_horas_registradas': horas_realizadas == Decimal('0'),
        'situacao': acao,
    }


def get_tabela_projetos(
    programa_id, page=1, page_size=10, sort_by="nome_projeto", sort_dir="asc"
):
    get_object_or_404(DimPrograma, id=programa_id)
    page = normalizar_pagina(page)

    projetos = DimProjeto.objects.filter(programa_id=programa_id)
    if sort_by in CAMPOS_ORDENACAO_DB:
        order_field = sort_by if sort_dir == "asc" else f"-{sort_by}"
        projetos = projetos.order_by(order_field)
    else:
        projetos = projetos.order_by("id")

    total_items = projetos.count()

    if sort_by == "acao":
        projetos_iter = projetos
    else:
        total_pages, start, end = calcular_paginacao(total_items, page, page_size)
        projetos_iter = projetos[start:end]

    hoje = date.today()
    resultado = [_processar_projeto(p, hoje) for p in projetos_iter]

    if sort_by == "acao":
        reverse = sort_dir == "desc"
        resultado.sort(key=lambda p: ACAO_ORDEM.get(p["acao"], 99), reverse=reverse)
        total_pages, start, end = calcular_paginacao(total_items, page, page_size)
        resultado = resultado[start:end]

    return {
        "count": total_items,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "results": resultado,
    }


def get_distribuicao_status(programa_id):
    status_counts = list(
        DimProjeto.objects.filter(programa_id=programa_id)
        .values("status")
        .annotate(total=Count("id"))
    )

    status_dict = {item["status"]: item["total"] for item in status_counts}
    total_geral = sum(item["total"] for item in status_counts)

    resultado = []
    for status in STATUS_PADRAO:
        quantidade = status_dict.get(status, 0)
        percentual = (
            round((quantidade / total_geral) * 100, 1) if total_geral > 0 else 0
        )
        resultado.append(
            {
                "status": status,
                "quantidade": quantidade,
                "percentual": percentual,
                "cor": STATUS_CORES[status],
            }
        )

    resultado = [r for r in resultado if r["quantidade"] > 0]

    return {
        "total": total_geral,
        "status": resultado,
    }


def get_burnup_horas_programas():
    horas_qs = (
        FatoHoras.objects.values(
            "programa__codigo_programa",
            "programa__nome_programa",
            "tempo__ano",
            "tempo__mes",
        )
        .annotate(horas_periodo=Sum("horas_trabalhadas"))
        .order_by("tempo__ano", "tempo__mes")
    )

    grupos_por_data = {}
    horas_acumuladas = {}
    for row in horas_qs:
        codigo = row["programa__codigo_programa"]
        nome = row["programa__nome_programa"]
        date_str = f'{row["tempo__mes"]:02d}/{row["tempo__ano"]}'

        date_group = grupos_por_data.get(date_str)
        if date_group is None:
            date_group = {"date_str": date_str, "values": []}
            grupos_por_data[date_str] = date_group

        horas = horas_acumuladas.get(codigo, 0.0) + float(row["horas_periodo"] or 0)
        horas_acumuladas[codigo] = horas

        date_group["values"].append(
            {
                "codigo_programa": codigo,
                "nome_programa": nome,
                "horas": horas,
            }
        )

    return list(grupos_por_data.values())


def get_burnup_custo_programas():
    horas_qs = FatoHoras.objects.values(
        "programa__codigo_programa",
        "programa__nome_programa",
        "tempo__ano",
        "tempo__mes",
    ).annotate(custo_periodo=Sum("custo_horas"))

    compras_qs = (
        FatoCompras.objects.exclude(status__nome_status="Cancelado")
        .filter(projeto__programa__isnull=False)
        .values(
            "projeto__programa__codigo_programa",
            "projeto__programa__nome_programa",
            "tempo__ano",
            "tempo__mes",
        )
        .annotate(custo_periodo=Sum("valor_alocado"))
    )

    custos_por_periodo = {}

    def acumular(rows, campo_codigo, campo_nome):
        for row in rows:
            codigo = row[campo_codigo]
            if codigo is None:
                continue
            periodo = (row["tempo__ano"], row["tempo__mes"])
            programas = custos_por_periodo.setdefault(periodo, {})
            info = programas.setdefault(
                codigo, {"nome": row[campo_nome], "custo": Decimal(0.0)}
            )
            info["custo"] += Decimal(row["custo_periodo"] or 0)

    acumular(horas_qs, "programa__codigo_programa", "programa__nome_programa")
    acumular(
        compras_qs,
        "projeto__programa__codigo_programa",
        "projeto__programa__nome_programa",
    )

    custo_acumulado = {}
    burnup_list = []
    for ano, mes in sorted(custos_por_periodo.keys()):
        grupo = {"date_str": f"{mes:02d}/{ano}", "values": []}
        for codigo, info in custos_por_periodo[(ano, mes)].items():
            custo_acumulado[codigo] = (
                Decimal(custo_acumulado.get(codigo, 0.0)) + info["custo"]
            )
            grupo["values"].append(
                {
                    "codigo_programa": codigo,
                    "nome_programa": info["nome"],
                    "custo": custo_acumulado[codigo],
                }
            )
        burnup_list.append(grupo)

    return burnup_list
