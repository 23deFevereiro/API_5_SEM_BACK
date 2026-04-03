import sys
import logging
import unicodedata
import pandas as pd
from pathlib import Path
from django.db import transaction
from django.core.management.base import BaseCommand

from api.models import (
    Programa, Projeto, Tarefa, TempoTarefa,
    Fornecedor, Material, SolicitacaoCompra, PedidoCompra,
    ComprasProjeto, EmpenhoMaterial, EstoqueMaterialProjeto,
)

logger = logging.getLogger(__name__)

CSV_DIR = Path(__file__).resolve().parents[4] / "data" / "csv"

_STATUS_VALIDOS = {"ativo", "inativo", "obsoleto", "concluido", "cancelado", "em andamento", "pendente"}



def corrigir_inconsistencias(df: pd.DataFrame, contexto: str) -> pd.DataFrame:
    return df


def ler_csv(nome_arquivo: str) -> pd.DataFrame:
    caminho = CSV_DIR / nome_arquivo
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    amostra = caminho.read_text(encoding="utf-8", errors="replace")[:500]
    sep = ";" if amostra.count(";") > amostra.count(",") else ","
    df = pd.read_csv(caminho, sep=sep, encoding="utf-8", dtype=str)
    logger.info(f"[{nome_arquivo}] {len(df)} registros lidos.")
    return df


def normalizar_string(valor: str) -> str:
    if not isinstance(valor, str):
        return valor
    valor = valor.strip()
    valor = unicodedata.normalize("NFC", valor)
    return valor


def normalizar_status(valor: str) -> str:
    if not isinstance(valor, str):
        return valor
    normalizado = valor.strip().lower()
    return valor.strip() if normalizado in _STATUS_VALIDOS else valor.strip()


def limpar_strings(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(lambda v: normalizar_string(v) if pd.notna(v) else v)
    if "status" in df.columns:
        df["status"] = df["status"].apply(lambda v: normalizar_status(v) if pd.notna(v) else v)
    return df


def para_data(serie: pd.Series) -> pd.Series:
    return pd.to_datetime(serie, errors="coerce", dayfirst=False)


def para_inteiro(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce").astype("Int64")


def para_decimal(serie: pd.Series) -> pd.Series:
    serie = serie.str.replace(",", ".", regex=False) if serie.dtype == object else serie
    return pd.to_numeric(serie, errors="coerce")


def logar_nulos(df: pd.DataFrame, contexto: str) -> None:
    nulos = df.isnull().sum()
    nulos = nulos[nulos > 0]
    if not nulos.empty:
        logger.warning(f"[{contexto}] Nulos após conversão:\n{nulos.to_string()}")


def validar_colunas(df: pd.DataFrame, obrigatorias: list[str], contexto: str) -> None:
    ausentes = [col for col in obrigatorias if col not in df.columns]
    if ausentes:
        raise ValueError(f"[{contexto}] Colunas obrigatórias ausentes no CSV: {ausentes}")


def safe_date(valor) -> object:
    return valor if pd.notna(valor) else None


def safe_val(valor) -> object:
    return valor if pd.notna(valor) else None


# ---------------------------------------------------------------------------
# Funções de ingestão por entidade
# ---------------------------------------------------------------------------

@transaction.atomic
def ingerir_programas() -> None:
    df = ler_csv("programas.csv")
    validar_colunas(df, ["codigo_programa", "nome_programa", "gerente_programa", "status"], "programas")
    df = limpar_strings(df)
    if "id" in df.columns:
        df["id"] = para_inteiro(df["id"])
    df["data_inicio"]       = para_data(df["data_inicio"])
    df["data_fim_prevista"] = para_data(df["data_fim_prevista"])
    logar_nulos(df, "programas")
    df = corrigir_inconsistencias(df, "programas")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            lookup = (
                {"id": row["id"]}
                if "id" in row and pd.notna(row["id"])
                else {"codigo_programa": row["codigo_programa"]}
            )
            defaults = {
                "codigo_programa":   row["codigo_programa"],
                "nome_programa":     row["nome_programa"],
                "gerente_programa":  row["gerente_programa"],
                "gerente_tecnico":   safe_val(row.get("gerente_tecnico")),
                "data_inicio":       safe_date(row["data_inicio"]),
                "data_fim_prevista": safe_date(row["data_fim_prevista"]),
                "status":            row["status"],
            }
            _, created = Programa.objects.update_or_create(**lookup, defaults=defaults)
            if created:
                criados += 1
            else:
                atualizados += 1
        except Exception as e:
            logger.error(f"[programas] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[programas] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_fornecedores() -> None:
    df = ler_csv("fornecedores.csv")
    validar_colunas(df, ["codigo_fornecedor", "razao_social", "cidade", "estado", "categoria", "status"], "fornecedores")
    df = limpar_strings(df)
    if "id" in df.columns:
        df["id"] = para_inteiro(df["id"])
    logar_nulos(df, "fornecedores")
    df = corrigir_inconsistencias(df, "fornecedores")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            lookup = (
                {"id": row["id"]}
                if "id" in row and pd.notna(row["id"])
                else {"codigo_fornecedor": row["codigo_fornecedor"]}
            )
            defaults = {
                "codigo_fornecedor": row["codigo_fornecedor"],
                "razao_social":      row["razao_social"],
                "cidade":            row["cidade"],
                "estado":            row["estado"].upper()[:2] if pd.notna(row.get("estado")) else row.get("estado"),
                "categoria":         row["categoria"],
                "status":            row["status"],
            }
            _, created = Fornecedor.objects.update_or_create(**lookup, defaults=defaults)
            if created:
                criados += 1
            else:
                atualizados += 1
        except Exception as e:
            logger.error(f"[fornecedores] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[fornecedores] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_materiais() -> None:
    df = ler_csv("materiais.csv")
    validar_colunas(df, ["codigo_material", "descricao", "categoria", "fabricante", "status"], "materiais")
    df = limpar_strings(df)
    if "id" in df.columns:
        df["id"] = para_inteiro(df["id"])
    df["custo_estimado"] = para_decimal(df["custo_estimado"])
    logar_nulos(df, "materiais")
    df = corrigir_inconsistencias(df, "materiais")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            lookup = (
                {"id": row["id"]}
                if "id" in row and pd.notna(row["id"])
                else {"codigo_material": row["codigo_material"]}
            )
            defaults = {
                "codigo_material": row["codigo_material"],
                "descricao":       row["descricao"],
                "categoria":       row["categoria"],
                "fabricante":      row["fabricante"],
                "custo_estimado":  safe_val(row["custo_estimado"]),
                "status":          row["status"],
            }
            _, created = Material.objects.update_or_create(**lookup, defaults=defaults)
            if created:
                criados += 1
            else:
                atualizados += 1
        except Exception as e:
            logger.error(f"[materiais] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[materiais] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_projetos() -> None:
    df = ler_csv("projetos.csv")
    validar_colunas(df, ["codigo_projeto", "nome_projeto", "programa_id", "responsavel", "status"], "projetos")
    df = limpar_strings(df)
    if "id" in df.columns:
        df["id"] = para_inteiro(df["id"])
    df["programa_id"]       = para_inteiro(df["programa_id"])
    df["custo_hora"]        = para_decimal(df["custo_hora"])
    df["data_inicio"]       = para_data(df["data_inicio"])
    df["data_fim_prevista"] = para_data(df["data_fim_prevista"])
    logar_nulos(df, "projetos")
    df = corrigir_inconsistencias(df, "projetos")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            programa = Programa.objects.get(id=row["programa_id"])
            lookup = (
                {"id": row["id"]}
                if "id" in row and pd.notna(row["id"])
                else {"codigo_projeto": row["codigo_projeto"]}
            )
            defaults = {
                "codigo_projeto":    row["codigo_projeto"],
                "nome_projeto":      row["nome_projeto"],
                "programa":          programa,
                "responsavel":       row["responsavel"],
                "custo_hora":        safe_val(row["custo_hora"]),
                "data_inicio":       safe_date(row["data_inicio"]),
                "data_fim_prevista": safe_date(row["data_fim_prevista"]),
                "status":            row["status"],
            }
            _, created = Projeto.objects.update_or_create(**lookup, defaults=defaults)
            if created:
                criados += 1
            else:
                atualizados += 1
        except Programa.DoesNotExist:
            logger.error(f"[projetos] Programa id={row['programa_id']} não encontrada — linha ignorada")
            erros += 1
        except Exception as e:
            logger.error(f"[projetos] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[projetos] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_tarefas() -> None:
    df = ler_csv("tarefas_projeto.csv")
    validar_colunas(df, ["codigo_tarefa", "projeto_id", "titulo", "responsavel", "status"], "tarefas_projeto")
    df = limpar_strings(df)
    if "id" in df.columns:
        df["id"] = para_inteiro(df["id"])
    df["projeto_id"]        = para_inteiro(df["projeto_id"])
    df["estimativa_horas"]  = para_decimal(df["estimativa_horas"])
    df["data_inicio"]       = para_data(df["data_inicio"])
    df["data_fim_prevista"] = para_data(df["data_fim_prevista"])
    logar_nulos(df, "tarefas_projeto")
    df = corrigir_inconsistencias(df, "tarefas_projeto")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            projeto = Projeto.objects.get(id=row["projeto_id"])
            lookup = (
                {"id": row["id"]}
                if "id" in row and pd.notna(row["id"])
                else {"codigo_tarefa": row["codigo_tarefa"]}
            )
            defaults = {
                "codigo_tarefa":     row["codigo_tarefa"],
                "projeto":           projeto,
                "titulo":            row["titulo"],
                "responsavel":       row["responsavel"],
                "estimativa_horas":  safe_val(row["estimativa_horas"]),
                "data_inicio":       safe_date(row["data_inicio"]),
                "data_fim_prevista": safe_date(row["data_fim_prevista"]),
                "status":            row["status"],
            }
            _, created = Tarefa.objects.update_or_create(**lookup, defaults=defaults)
            if created:
                criados += 1
            else:
                atualizados += 1
        except Projeto.DoesNotExist:
            logger.error(f"[tarefas] Projeto id={row['projeto_id']} não encontrada — linha ignorada")
            erros += 1
        except Exception as e:
            logger.error(f"[tarefas] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[tarefas] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_tempo_tarefas() -> None:
    df = ler_csv("tempo_tarefas.csv")
    validar_colunas(df, ["tarefa_id", "usuario", "data", "horas_trabalhadas"], "tempo_tarefas")
    df = limpar_strings(df)
    df["tarefa_id"]         = para_inteiro(df["tarefa_id"])
    df["horas_trabalhadas"] = para_decimal(df["horas_trabalhadas"])
    df["data"]              = para_data(df["data"])
    logar_nulos(df, "tempo_tarefas")
    df = corrigir_inconsistencias(df, "tempo_tarefas")

    criados = atualizados = erros = 0
    for idx, row in df.iterrows():
        if pd.isna(row["data"]):
            logger.warning(f"[tempo_tarefas] linha {idx}: campo 'data' nulo — linha ignorada")
            erros += 1
            continue
        if pd.isna(row["tarefa_id"]):
            logger.warning(f"[tempo_tarefas] linha {idx}: campo 'tarefa_id' nulo — linha ignorada")
            erros += 1
            continue
        try:
            tarefa = Tarefa.objects.get(id=row["tarefa_id"])
            _, created = TempoTarefa.objects.update_or_create(
                tarefa=tarefa,
                usuario=row["usuario"],
                data=row["data"].date(),
                defaults={
                    "horas_trabalhadas": safe_val(row["horas_trabalhadas"]),
                },
            )
            if created:
                criados += 1
            else:
                atualizados += 1
        except Tarefa.DoesNotExist:
            logger.error(f"[tempo_tarefas] Tarefa id={row['tarefa_id']} não encontrada — linha ignorada")
            erros += 1
        except Exception as e:
            logger.error(f"[tempo_tarefas] linha {idx}: {e}")
            erros += 1
    logger.info(f"[tempo_tarefas] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_solicitacoes_compra() -> None:
    df = ler_csv("solicitacoes_compra.csv")
    validar_colunas(df, ["numero_solicitacao", "projeto_id", "material_id", "quantidade", "prioridade", "status"], "solicitacoes_compra")
    df = limpar_strings(df)
    if "id" in df.columns:
        df["id"] = para_inteiro(df["id"])
    df["projeto_id"]       = para_inteiro(df["projeto_id"])
    df["material_id"]      = para_inteiro(df["material_id"])
    df["quantidade"]       = para_inteiro(df["quantidade"])
    df["data_solicitacao"] = para_data(df["data_solicitacao"])
    logar_nulos(df, "solicitacoes_compra")
    df = corrigir_inconsistencias(df, "solicitacoes_compra")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            projeto  = Projeto.objects.get(id=row["projeto_id"])
            material = Material.objects.get(id=row["material_id"])
            lookup = (
                {"id": row["id"]}
                if "id" in row and pd.notna(row["id"])
                else {"numero_solicitacao": row["numero_solicitacao"]}
            )
            defaults = {
                "numero_solicitacao": row["numero_solicitacao"],
                "projeto":            projeto,
                "material":           material,
                "quantidade":         safe_val(row["quantidade"]),
                "data_solicitacao":   safe_date(row["data_solicitacao"]),
                "prioridade":         row["prioridade"],
                "status":             row["status"],
            }
            _, created = SolicitacaoCompra.objects.update_or_create(**lookup, defaults=defaults)
            if created:
                criados += 1
            else:
                atualizados += 1
        except (Projeto.DoesNotExist, Material.DoesNotExist) as e:
            logger.error(f"[solicitacoes_compra] FK não encontrada linha {row.get('id', '?')}: {e} — linha ignorada")
            erros += 1
        except Exception as e:
            logger.error(f"[solicitacoes_compra] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[solicitacoes_compra] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_pedidos_compra() -> None:
    df = ler_csv("pedidos_compra.csv")
    validar_colunas(df, ["numero_pedido", "solicitacao_id", "fornecedor_id", "status"], "pedidos_compra")
    df = limpar_strings(df)
    if "id" in df.columns:
        df["id"] = para_inteiro(df["id"])
    df["solicitacao_id"]        = para_inteiro(df["solicitacao_id"])
    df["fornecedor_id"]         = para_inteiro(df["fornecedor_id"])
    df["data_pedido"]           = para_data(df["data_pedido"])
    df["data_previsao_entrega"] = para_data(df["data_previsao_entrega"])
    df["valor_total"]           = para_decimal(df["valor_total"])
    logar_nulos(df, "pedidos_compra")
    df = corrigir_inconsistencias(df, "pedidos_compra")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            fornecedor  = Fornecedor.objects.get(id=row["fornecedor_id"])
            solicitacao = SolicitacaoCompra.objects.get(id=row["solicitacao_id"])
            lookup = (
                {"id": row["id"]}
                if "id" in row and pd.notna(row["id"])
                else {"numero_pedido": row["numero_pedido"]}
            )
            defaults = {
                "numero_pedido":         row["numero_pedido"],
                "solicitacao":           solicitacao,
                "fornecedor":            fornecedor,
                "data_pedido":           safe_date(row["data_pedido"]),
                "data_previsao_entrega": safe_date(row["data_previsao_entrega"]),
                "valor_total":           safe_val(row["valor_total"]),
                "status":                row["status"],
            }
            _, created = PedidoCompra.objects.update_or_create(**lookup, defaults=defaults)
            if created:
                criados += 1
            else:
                atualizados += 1
        except (Fornecedor.DoesNotExist, SolicitacaoCompra.DoesNotExist) as e:
            logger.error(f"[pedidos_compra] FK não encontrada linha {row.get('id', '?')}: {e} — linha ignorada")
            erros += 1
        except Exception as e:
            logger.error(f"[pedidos_compra] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[pedidos_compra] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_compras_projeto() -> None:
    df = ler_csv("compras_projeto.csv")
    validar_colunas(df, ["pedido_compra_id", "projeto_id", "valor_alocado"], "compras_projeto")
    df = limpar_strings(df)
    df["pedido_compra_id"] = para_inteiro(df["pedido_compra_id"])
    df["projeto_id"]       = para_inteiro(df["projeto_id"])
    df["valor_alocado"]    = para_decimal(df["valor_alocado"])
    logar_nulos(df, "compras_projeto")
    df = corrigir_inconsistencias(df, "compras_projeto")

    criados = atualizados = erros = 0
    for idx, row in df.iterrows():
        try:
            projeto = Projeto.objects.get(id=row["projeto_id"])
            pedido  = PedidoCompra.objects.get(id=row["pedido_compra_id"])
            _, created = ComprasProjeto.objects.update_or_create(
                projeto=projeto,
                pedido=pedido,
                defaults={
                    "valor_alocado": safe_val(row["valor_alocado"]),
                },
            )
            if created:
                criados += 1
            else:
                atualizados += 1
        except (Projeto.DoesNotExist, PedidoCompra.DoesNotExist) as e:
            logger.error(f"[compras_projeto] FK não encontrada linha {idx}: {e} — linha ignorada")
            erros += 1
        except Exception as e:
            logger.error(f"[compras_projeto] linha {idx}: {e}")
            erros += 1
    logger.info(f"[compras_projeto] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_empenho_materiais() -> None:
    df = ler_csv("empenho_materiais.csv")
    validar_colunas(df, ["projeto_id", "material_id", "quantidade_empenhada", "data_empenho"], "empenho_materiais")
    df = limpar_strings(df)
    df["projeto_id"]           = para_inteiro(df["projeto_id"])
    df["material_id"]          = para_inteiro(df["material_id"])
    df["quantidade_empenhada"] = para_inteiro(df["quantidade_empenhada"])
    df["data_empenho"]         = para_data(df["data_empenho"])
    logar_nulos(df, "empenho_materiais")
    df = corrigir_inconsistencias(df, "empenho_materiais")

    criados = atualizados = erros = 0
    for idx, row in df.iterrows():
        try:
            projeto  = Projeto.objects.get(id=row["projeto_id"])
            material = Material.objects.get(id=row["material_id"])
            _, created = EmpenhoMaterial.objects.update_or_create(
                projeto=projeto,
                material=material,
                defaults={
                    "quantidade_empenhada": safe_val(row["quantidade_empenhada"]),
                    "data_empenho":         row["data_empenho"].date() if pd.notna(row["data_empenho"]) else None,
                },
            )
            if created:
                criados += 1
            else:
                atualizados += 1
        except (Projeto.DoesNotExist, Material.DoesNotExist) as e:
            logger.error(f"[empenho_materiais] FK não encontrada linha {idx}: {e} — linha ignorada")
            erros += 1
        except Exception as e:
            logger.error(f"[empenho_materiais] linha {idx}: {e}")
            erros += 1
    logger.info(f"[empenho_materiais] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_estoque_materiais_projeto() -> None:
    df = ler_csv("estoque_materiais_projeto.csv")
    validar_colunas(df, ["projeto_id", "material_id", "quantidade", "localizacao"], "estoque_materiais_projeto")
    df = limpar_strings(df)
    df["projeto_id"]  = para_inteiro(df["projeto_id"])
    df["material_id"] = para_inteiro(df["material_id"])
    df["quantidade"]  = para_inteiro(df["quantidade"])
    logar_nulos(df, "estoque_materiais_projeto")
    df = corrigir_inconsistencias(df, "estoque_materiais_projeto")

    criados = atualizados = erros = 0
    for idx, row in df.iterrows():
        try:
            projeto  = Projeto.objects.get(id=row["projeto_id"])
            material = Material.objects.get(id=row["material_id"])
            _, created = EstoqueMaterialProjeto.objects.update_or_create(
                projeto=projeto,
                material=material,
                defaults={
                    "quantidade":  safe_val(row["quantidade"]),
                    "localizacao": row["localizacao"],
                },
            )
            if created:
                criados += 1
            else:
                atualizados += 1
        except (Projeto.DoesNotExist, Material.DoesNotExist) as e:
            logger.error(f"[estoque_materiais_projeto] FK não encontrada linha {idx}: {e} — linha ignorada")
            erros += 1
        except Exception as e:
            logger.error(f"[estoque_materiais_projeto] linha {idx}: {e}")
            erros += 1
    logger.info(f"[estoque_materiais_projeto] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def calcular_e_atualizar_lead_time() -> None:
    from django.db.models import Avg, F, ExpressionWrapper, fields as dj_fields

    atualizados = sem_pedido = erros = 0

    lead_times = (
        PedidoCompra.objects
        .filter(
            data_pedido__isnull=False,
            data_previsao_entrega__isnull=False,
            data_previsao_entrega__gte=F("data_pedido"),
        )
        .annotate(
            dias=ExpressionWrapper(
                F("data_previsao_entrega") - F("data_pedido"),
                output_field=dj_fields.DurationField(),
            )
        )
        .values("solicitacao__material_id")
        .annotate(media_dias=Avg("dias"))
    )

    lead_time_por_material = {
        entry["solicitacao__material_id"]: entry["media_dias"]
        for entry in lead_times
        if entry["media_dias"] is not None
    }

    for material in Material.objects.all():
        try:
            if material.id not in lead_time_por_material:
                sem_pedido += 1
                continue
            duracao = lead_time_por_material[material.id]
            material.lead_time = round(duracao.days if hasattr(duracao, "days") else duracao)
            material.save(update_fields=["lead_time"])
            atualizados += 1
        except Exception as e:
            logger.error(f"[lead_time] material id={material.id}: {e}")
            erros += 1

    logger.info(f"[lead_time] atualizados={atualizados} sem_pedido={sem_pedido} erros={erros}")


# ---------------------------------------------------------------------------
# Management Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Ingere os arquivos CSV nas tabelas do banco. Uso: python manage.py ingest_data"

    def handle(self, *args, **kwargs):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

        etapas = [
            ("programas",                 ingerir_programas),
            ("fornecedores",              ingerir_fornecedores),
            ("materiais",                 ingerir_materiais),
            ("projetos",                  ingerir_projetos),
            ("tarefas_projeto",           ingerir_tarefas),
            ("tempo_tarefas",             ingerir_tempo_tarefas),
            ("solicitacoes_compra",       ingerir_solicitacoes_compra),
            ("empenho_materiais",         ingerir_empenho_materiais),
            ("estoque_materiais_projeto", ingerir_estoque_materiais_projeto),
            ("pedidos_compra",            ingerir_pedidos_compra),
            ("lead_time",                 calcular_e_atualizar_lead_time),
            ("compras_projeto",           ingerir_compras_projeto),
        ]

        self.stdout.write("=== Iniciando ingestão de dados ===")
        for nome, funcao in etapas:
            self.stdout.write(f"--- {nome} ---")
            try:
                funcao()
            except Exception as e:
                self.stderr.write(f"Falha crítica em '{nome}': {e}")
                raise
        self.stdout.write("=== Ingestão concluída com sucesso ===")