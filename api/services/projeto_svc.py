from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.shortcuts import get_object_or_404

from ..models import DimMaterial, DimProjeto, FatoHoras, FatoMateriais
from ..utils.pagination import calcular_paginacao, normalizar_pagina


def listar_projetos(search="", programa_id=None):
    projetos = DimProjeto.objects.all()
    if search:
        projetos = projetos.filter(nome_projeto__icontains=search)
    if programa_id is not None:
        projetos = projetos.filter(programa=programa_id)
    return list(projetos.values("id", "codigo_projeto", "nome_projeto"))


def get_overview_data_all(programa_id=None):
    fatos = FatoMateriais.objects.filter(
        projeto__status__in=["Em andamento", "Concluído"]
    )
    if programa_id is not None:
        fatos = fatos.filter(programa_id=programa_id)

    cost_material = (
        fatos.values(
            "projeto__codigo_projeto",
            "projeto__nome_projeto",
            "tempo__ano",
            "tempo__mes",
        )
        .annotate(cost=Sum("custo_materiais"))
        .order_by("tempo__ano", "tempo__mes")
    )

    cost_list = []
    total_cost_dict = {}
    for material_data in cost_material:
        date_str = f'{material_data["tempo__mes"]:02d}/{material_data["tempo__ano"]}'

        date_group = [group for group in cost_list if group["date_str"] == date_str]
        if not date_group:
            date_group = {"date_str": date_str, "values": []}
            cost_list.append(date_group)
        else:
            date_group = date_group[0]

        codigo_projeto = material_data["projeto__codigo_projeto"]
        if codigo_projeto not in total_cost_dict:
            total_cost_dict[codigo_projeto] = 0

        cost = total_cost_dict[codigo_projeto] + float(material_data["cost"])
        total_cost_dict[codigo_projeto] = cost

        date_group["values"].append(
            {
                "codigo_projeto": codigo_projeto,
                "nome_projeto": material_data["projeto__nome_projeto"],
                "cost": cost,
            }
        )

    return cost_list


def get_resumo_projeto(projeto_id):
    get_object_or_404(DimProjeto, id=projeto_id)

    horas_agg = FatoHoras.objects.filter(projeto_id=projeto_id).aggregate(
        horas=Sum("horas_trabalhadas"),
        custo=Sum("custo_horas"),
    )

    tempo_total = horas_agg["horas"] or Decimal("0")
    custo_mao_de_obra = horas_agg["custo"] or Decimal("0")

    custo_materiais = FatoMateriais.objects.filter(projeto_id=projeto_id).aggregate(
        total=Sum("custo_materiais")
    )["total"] or Decimal("0")

    return {
        "custo_total": custo_mao_de_obra + custo_materiais,
        "tempo_total": tempo_total,
    }


def formatar_material(item):
    return {
        "nome_material": item["material__descricao"],
        "quantidade": item["quantidade"],
        "custo_total_estimado": float(item["custo_total_estimado"] or 0),
    }


def get_materiais_projeto(
    projeto_id, page=1, page_size=10, data_inicio=None, data_fim=None, material=None
):
    page = normalizar_pagina(page)

    base_qs = FatoMateriais.objects.filter(projeto_id=projeto_id)
    if data_inicio:
        base_qs = base_qs.filter(tempo__data__gte=data_inicio)
    if data_fim:
        base_qs = base_qs.filter(tempo__data__lte=data_fim)
    if material:
        base_qs = base_qs.filter(material__descricao__icontains=material)

    materiais_qs = (
        base_qs.values("material_id", "material__descricao", "material__custo_estimado")
        .annotate(quantidade=Sum("quantidade_empenhada"))
        .annotate(
            custo_total_estimado=ExpressionWrapper(
                F("quantidade") * F("material__custo_estimado"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        .order_by("material__descricao")
    )

    total_items = materiais_qs.count()
    total_pages, start, end = calcular_paginacao(total_items, page, page_size)

    resultados = [formatar_material(item) for item in materiais_qs[start:end]]

    return {
        "count": total_items,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "results": resultados,
    }


def get_materiais_disponiveis(projeto_id):
    return list(
        DimMaterial.objects.filter(fatomateriais__projeto_id=projeto_id)
        .distinct()
        .order_by("descricao")
        .values("id", "descricao")
    )
