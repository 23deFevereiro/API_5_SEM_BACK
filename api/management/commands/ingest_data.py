import sys
import logging
import pandas as pd
from pathlib import Path
from django.db import transaction
from django.core.management.base import BaseCommand

from .models import (
    ProgramaEmpresa, ProjetoPrograma, TarefaProjeto, TempoTarefa,
    Fornecedor, Material, SolicitacaoCompra, PedidoCompra,
    CompraProjeto, EmpenhoMaterial, EstoqueMaterialProjeto,
)

logger = logging.getLogger(__name__)

CSV_DIR = Path(__file__).resolve().parents[4] / "data" / "csv"


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


def limpar_strings(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    return df


def para_data(serie: pd.Series) -> pd.Series:
    return pd.to_datetime(serie, errors="coerce", dayfirst=False)


def para_inteiro(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce").astype("Int64")


def para_decimal(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce")


def logar_nulos(df: pd.DataFrame, contexto: str) -> None:
    nulos = df.isnull().sum()
    nulos = nulos[nulos > 0]
    if not nulos.empty:
        logger.warning(f"[{contexto}] Nulos após conversão:\n{nulos.to_string()}")


@transaction.atomic
def ingerir_programas() -> None:
    df = ler_csv("programas.csv")
    df = limpar_strings(df)
    df["data_inicio"]       = para_data(df["data_inicio"])
    df["data_fim_prevista"] = para_data(df["data_fim_prevista"])
    logar_nulos(df, "programas")
    df = corrigir_inconsistencias(df, "programas")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            _, created = ProgramaEmpresa.objects.update_or_create(
                codigo_programa=row["codigo_programa"],
                defaults={
                    "nome_programa":     row["nome_programa"],
                    "gerente_programa":  row["gerente_programa"],
                    "gerente_tecnico":   row.get("gerente_tecnico"),
                    "data_inicio":       row["data_inicio"] if pd.notna(row["data_inicio"]) else None,
                    "data_fim_prevista": row["data_fim_prevista"] if pd.notna(row["data_fim_prevista"]) else None,
                    "status":            row["status"],
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except Exception as e:
            logger.error(f"[programas] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[programas] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_fornecedores() -> None:
    df = ler_csv("fornecedores.csv")
    df = limpar_strings(df)
    logar_nulos(df, "fornecedores")
    df = corrigir_inconsistencias(df, "fornecedores")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            _, created = Fornecedor.objects.update_or_create(
                codigo_fornecedor=row["codigo_fornecedor"],
                defaults={
                    "razao_social": row["razao_social"],
                    "cidade":       row["cidade"],
                    "estado":       row["estado"],
                    "categoria":    row["categoria"],
                    "status":       row["status"],
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except Exception as e:
            logger.error(f"[fornecedores] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[fornecedores] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_materiais() -> None:
    df = ler_csv("materiais.csv")
    df = limpar_strings(df)
    df["custo_estimado"] = para_decimal(df["custo_estimado"])
    logar_nulos(df, "materiais")
    df = corrigir_inconsistencias(df, "materiais")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            _, created = Material.objects.update_or_create(
                codigo_material=row["codigo_material"],
                defaults={
                    "descricao":      row["descricao"],
                    "categoria":      row["categoria"],
                    "fabricante":     row["fabricante"],
                    "custo_estimado": row["custo_estimado"] if pd.notna(row["custo_estimado"]) else None,
                    "status":         row["status"],
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except Exception as e:
            logger.error(f"[materiais] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[materiais] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_projetos() -> None:
    df = ler_csv("projetos.csv")
    df = limpar_strings(df)
    df["programa_id"]       = para_inteiro(df["programa_id"])
    df["custo_hora"]        = para_decimal(df["custo_hora"])
    df["data_inicio"]       = para_data(df["data_inicio"])
    df["data_fim_prevista"] = para_data(df["data_fim_prevista"])
    logar_nulos(df, "projetos")
    df = corrigir_inconsistencias(df, "projetos")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            programa = ProgramaEmpresa.objects.get(id=row["programa_id"])
            _, created = ProjetoPrograma.objects.update_or_create(
                codigo_projeto=row["codigo_projeto"],
                defaults={
                    "nome_projeto":      row["nome_projeto"],
                    "programa":          programa,
                    "responsavel":       row["responsavel"],
                    "custo_hora":        row["custo_hora"] if pd.notna(row["custo_hora"]) else None,
                    "data_inicio":       row["data_inicio"] if pd.notna(row["data_inicio"]) else None,
                    "data_fim_prevista": row["data_fim_prevista"] if pd.notna(row["data_fim_prevista"]) else None,
                    "status":            row["status"],
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except ProgramaEmpresa.DoesNotExist:
            logger.error(f"[projetos] ProgramaEmpresa id={row['programa_id']} não encontrado")
            erros += 1
        except Exception as e:
            logger.error(f"[projetos] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[projetos] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_tarefas() -> None:
    df = ler_csv("tarefas_projeto.csv")
    df = limpar_strings(df)
    df["projeto_id"]        = para_inteiro(df["projeto_id"])
    df["estimativa_horas"]  = para_decimal(df["estimativa_horas"])
    df["data_inicio"]       = para_data(df["data_inicio"])
    df["data_fim_prevista"] = para_data(df["data_fim_prevista"])
    logar_nulos(df, "tarefas_projeto")
    df = corrigir_inconsistencias(df, "tarefas_projeto")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            projeto = ProjetoPrograma.objects.get(id=row["projeto_id"])
            _, created = TarefaProjeto.objects.update_or_create(
                codigo_tarefa=row["codigo_tarefa"],
                defaults={
                    "projeto":           projeto,
                    "titulo":            row["titulo"],
                    "responsavel":       row["responsavel"],
                    "estimativa_horas":  row["estimativa_horas"] if pd.notna(row["estimativa_horas"]) else None,
                    "data_inicio":       row["data_inicio"] if pd.notna(row["data_inicio"]) else None,
                    "data_fim_prevista": row["data_fim_prevista"] if pd.notna(row["data_fim_prevista"]) else None,
                    "status":            row["status"],
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except ProjetoPrograma.DoesNotExist:
            logger.error(f"[tarefas] ProjetoPrograma id={row['projeto_id']} não encontrado")
            erros += 1
        except Exception as e:
            logger.error(f"[tarefas] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[tarefas] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_tempo_tarefas() -> None:
    df = ler_csv("tempo_tarefas.csv")
    df = limpar_strings(df)
    df["tarefa_id"]         = para_inteiro(df["tarefa_id"])
    df["horas_trabalhadas"] = para_decimal(df["horas_trabalhadas"])
    df["data"]              = para_data(df["data"])
    logar_nulos(df, "tempo_tarefas")
    df = corrigir_inconsistencias(df, "tempo_tarefas")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            tarefa = TarefaProjeto.objects.get(id=row["tarefa_id"])
            _, created = TempoTarefa.objects.update_or_create(
                tarefa=tarefa,
                usuario=row["usuario"],
                data=row["data"].date() if pd.notna(row["data"]) else None,
                defaults={
                    "horas_trabalhadas": row["horas_trabalhadas"] if pd.notna(row["horas_trabalhadas"]) else None,
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except TarefaProjeto.DoesNotExist:
            logger.error(f"[tempo_tarefas] TarefaProjeto id={row['tarefa_id']} não encontrada")
            erros += 1
        except Exception as e:
            logger.error(f"[tempo_tarefas] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[tempo_tarefas] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_solicitacoes_compra() -> None:
    df = ler_csv("solicitacoes_compra.csv")
    df = limpar_strings(df)
    df["projeto_id"]       = para_inteiro(df["projeto_id"])
    df["material_id"]      = para_inteiro(df["material_id"])
    df["quantidade"]       = para_inteiro(df["quantidade"])
    df["data_solicitacao"] = para_data(df["data_solicitacao"])
    logar_nulos(df, "solicitacoes_compra")
    df = corrigir_inconsistencias(df, "solicitacoes_compra")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            projeto  = ProjetoPrograma.objects.get(id=row["projeto_id"])
            material = Material.objects.get(id=row["material_id"])
            _, created = SolicitacaoCompra.objects.update_or_create(
                numero_solicitacao=row["numero_solicitacao"],
                defaults={
                    "projeto":          projeto,
                    "material":         material,
                    "quantidade":       row["quantidade"] if pd.notna(row["quantidade"]) else None,
                    "data_solicitacao": row["data_solicitacao"] if pd.notna(row["data_solicitacao"]) else None,
                    "prioridade":       row["prioridade"],
                    "status":           row["status"],
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except (ProjetoPrograma.DoesNotExist, Material.DoesNotExist) as e:
            logger.error(f"[solicitacoes_compra] FK não encontrada linha {row.get('id', '?')}: {e}")
            erros += 1
        except Exception as e:
            logger.error(f"[solicitacoes_compra] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[solicitacoes_compra] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_pedidos_compra() -> None:
    df = ler_csv("pedidos_compra.csv")
    df = limpar_strings(df)
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
            _, created = PedidoCompra.objects.update_or_create(
                numero_pedido=row["numero_pedido"],
                defaults={
                    "solicitacao":           solicitacao,
                    "fornecedor":            fornecedor,
                    "data_pedido":           row["data_pedido"] if pd.notna(row["data_pedido"]) else None,
                    "data_previsao_entrega": row["data_previsao_entrega"] if pd.notna(row["data_previsao_entrega"]) else None,
                    "valor_total":           row["valor_total"] if pd.notna(row["valor_total"]) else None,
                    "status":                row["status"],
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except (Fornecedor.DoesNotExist, SolicitacaoCompra.DoesNotExist) as e:
            logger.error(f"[pedidos_compra] FK não encontrada linha {row.get('id', '?')}: {e}")
            erros += 1
        except Exception as e:
            logger.error(f"[pedidos_compra] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[pedidos_compra] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def calcular_e_atualizar_lead_time() -> None:
    atualizados = sem_pedido = erros = 0
    for material in Material.objects.all():
        try:
            pedidos = PedidoCompra.objects.filter(
                solicitacao__material=material,
                data_pedido__isnull=False,
                data_previsao_entrega__isnull=False,
            )
            if not pedidos.exists():
                sem_pedido += 1
                continue
            lead_times = [
                (p.data_previsao_entrega - p.data_pedido).days
                for p in pedidos
                if p.data_previsao_entrega >= p.data_pedido
            ]
            if not lead_times:
                sem_pedido += 1
                continue
            material.lead_time = round(sum(lead_times) / len(lead_times))
            material.save(update_fields=["lead_time"])
            atualizados += 1
        except Exception as e:
            logger.error(f"[lead_time] material id={material.id}: {e}")
            erros += 1
    logger.info(f"[lead_time] atualizados={atualizados} sem_pedido={sem_pedido} erros={erros}")


@transaction.atomic
def ingerir_compras_projeto() -> None:
    df = ler_csv("compras_projeto.csv")
    df = limpar_strings(df)
    df["pedido_compra_id"] = para_inteiro(df["pedido_compra_id"])
    df["projeto_id"]       = para_inteiro(df["projeto_id"])
    df["valor_alocado"]    = para_decimal(df["valor_alocado"])
    logar_nulos(df, "compras_projeto")
    df = corrigir_inconsistencias(df, "compras_projeto")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            projeto = ProjetoPrograma.objects.get(id=row["projeto_id"])
            pedido  = PedidoCompra.objects.get(id=row["pedido_compra_id"])
            _, created = CompraProjeto.objects.update_or_create(
                projeto=projeto,
                pedido=pedido,
                defaults={
                    "valor_alocado": row["valor_alocado"] if pd.notna(row["valor_alocado"]) else None,
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except (ProjetoPrograma.DoesNotExist, PedidoCompra.DoesNotExist) as e:
            logger.error(f"[compras_projeto] FK não encontrada linha {row.get('id', '?')}: {e}")
            erros += 1
        except Exception as e:
            logger.error(f"[compras_projeto] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[compras_projeto] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_empenho_materiais() -> None:
    df = ler_csv("empenho_materiais.csv")
    df = limpar_strings(df)
    df["projeto_id"]           = para_inteiro(df["projeto_id"])
    df["material_id"]          = para_inteiro(df["material_id"])
    df["quantidade_empenhada"] = para_inteiro(df["quantidade_empenhada"])
    df["data_empenho"]         = para_data(df["data_empenho"])
    logar_nulos(df, "empenho_materiais")
    df = corrigir_inconsistencias(df, "empenho_materiais")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            projeto  = ProjetoPrograma.objects.get(id=row["projeto_id"])
            material = Material.objects.get(id=row["material_id"])
            _, created = EmpenhoMaterial.objects.update_or_create(
                projeto=projeto,
                material=material,
                defaults={
                    "quantidade_empenhada": row["quantidade_empenhada"] if pd.notna(row["quantidade_empenhada"]) else None,
                    "data_empenho":         row["data_empenho"].date() if pd.notna(row["data_empenho"]) else None,
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except (ProjetoPrograma.DoesNotExist, Material.DoesNotExist) as e:
            logger.error(f"[empenho_materiais] FK não encontrada linha {row.get('id', '?')}: {e}")
            erros += 1
        except Exception as e:
            logger.error(f"[empenho_materiais] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[empenho_materiais] criados={criados} atualizados={atualizados} erros={erros}")


@transaction.atomic
def ingerir_estoque_materiais_projeto() -> None:
    df = ler_csv("estoque_materiais_projeto.csv")
    df = limpar_strings(df)
    df["projeto_id"]  = para_inteiro(df["projeto_id"])
    df["material_id"] = para_inteiro(df["material_id"])
    df["quantidade"]  = para_inteiro(df["quantidade"])
    logar_nulos(df, "estoque_materiais_projeto")
    df = corrigir_inconsistencias(df, "estoque_materiais_projeto")

    criados = atualizados = erros = 0
    for _, row in df.iterrows():
        try:
            projeto  = ProjetoPrograma.objects.get(id=row["projeto_id"])
            material = Material.objects.get(id=row["material_id"])
            _, created = EstoqueMaterialProjeto.objects.update_or_create(
                projeto=projeto,
                material=material,
                defaults={
                    "quantidade":  row["quantidade"] if pd.notna(row["quantidade"]) else None,
                    "localizacao": row["localizacao"],
                },
            )
            if created: criados += 1
            else: atualizados += 1
        except (ProjetoPrograma.DoesNotExist, Material.DoesNotExist) as e:
            logger.error(f"[estoque_materiais_projeto] FK não encontrada linha {row.get('id', '?')}: {e}")
            erros += 1
        except Exception as e:
            logger.error(f"[estoque_materiais_projeto] linha {row.get('id', '?')}: {e}")
            erros += 1
    logger.info(f"[estoque_materiais_projeto] criados={criados} atualizados={atualizados} erros={erros}")


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