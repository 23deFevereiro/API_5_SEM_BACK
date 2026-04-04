import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.db import transaction

from ..models import (
    Programa, Fornecedor, Material, Projeto, Tarefa,
    TempoTarefa, EstoqueMaterialProjeto, EmpenhoMaterial,
    PedidoCompra, SolicitacaoCompra, ComprasProjeto,
)

MODEL_MAP = {
    'programa': Programa,
    'fornecedor': Fornecedor,
    'material': Material,
    'projeto': Projeto,
    'tarefa': Tarefa,
    'tempo_tarefa': TempoTarefa,
    'estoque_material_projeto': EstoqueMaterialProjeto,
    'empenho_material': EmpenhoMaterial,
    'pedido_compra': PedidoCompra,
    'solicitacao_compra': SolicitacaoCompra,
    'compras_projeto': ComprasProjeto,
}

# Maps CSV column names ending in _id to the Django FK field name and lookup model/field
FK_COLUMNS = {
    'projeto': {
        'programa_id': ('programa', 'id', Programa),
    },
    'tarefa': {
        'projeto_id': ('projeto', 'id', Projeto),
    },
    'tempo_tarefa': {
        'tarefa_id': ('tarefa', 'id', Tarefa),
    },
    'estoque_material_projeto': {
        'projeto_id': ('projeto', 'id', Projeto),
        'material_id': ('material', 'id', Material),
    },
    'empenho_material': {
        'projeto_id': ('projeto', 'id', Projeto),
        'material_id': ('material', 'id', Material),
    },
    'pedido_compra': {
        'fornecedor_id': ('fornecedor', 'id', Fornecedor),
    },
    'solicitacao_compra': {
        'projeto_id': ('projeto', 'id', Projeto),
        'material_id': ('material', 'id', Material),
    },
    'compras_projeto': {
        'pedido_compra_id': ('pedido_compra', 'id', PedidoCompra),
        'projeto_id': ('projeto', 'id', Projeto),
    },
}

DATE_FIELDS = {
    'programa': ['data_inicio', 'data_fim_prevista'],
    'projeto': ['data_inicio', 'data_fim_prevista'],
    'tarefa': ['data_inicio', 'data_fim_prevista'],
    'tempo_tarefa': ['data'],
    'empenho_material': ['data_empenho'],
    'pedido_compra': ['data_pedido', 'data_previsao_entrega'],
    'solicitacao_compra': ['data_solicitacao'],
}

DECIMAL_FIELDS = {
    'material': ['custo_estimado'],
    'projeto': ['custo_hora'],
    'tarefa': ['estimativa_horas'],
    'tempo_tarefa': ['horas_trabalhadas'],
    'pedido_compra': ['valor_total'],
    'compras_projeto': ['valor_alocado'],
}

INTEGER_FIELDS = {
    'estoque_material_projeto': ['quantidade'],
    'empenho_material': ['quantidade_empenhada'],
    'solicitacao_compra': ['quantidade'],
}

SKIP_FIELDS = {'id'}

# Maps CSV filenames (without .csv) to model keys
FILENAME_TO_MODEL = {
    'programas': 'programa',
    'fornecedores': 'fornecedor',
    'materiais': 'material',
    'projetos': 'projeto',
    'tarefas_projeto': 'tarefa',
    'tempo_tarefas': 'tempo_tarefa',
    'estoque_materiais_projeto': 'estoque_material_projeto',
    'empenho_materiais': 'empenho_material',
    'pedidos_compra': 'pedido_compra',
    'solicitacoes_compra': 'solicitacao_compra',
    'compras_projeto': 'compras_projeto',
}

# Import order: parents first, then children
IMPORT_ORDER = [
    'programas',
    'fornecedores',
    'materiais',
    'projetos',
    'tarefas_projeto',
    'tempo_tarefas',
    'estoque_materiais_projeto',
    'empenho_materiais',
    'pedidos_compra',
    'solicitacoes_compra',
    'compras_projeto',
]

CSV_FOLDER = Path(settings.BASE_DIR) / 'corrigidos'


def get_available_models():
    return list(MODEL_MAP.keys())


def _detect_delimiter(text):
    first_line = text.split('\n', 1)[0]
    if ';' in first_line and ',' not in first_line:
        return ';'
    if ',' in first_line and ';' not in first_line:
        return ','
    if first_line.count(';') > first_line.count(','):
        return ';'
    return ','


def _parse_date(value):
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: '{value}'")


def _parse_decimal(value):
    cleaned = value.strip().replace(',', '.')
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"Invalid decimal value: '{value}'")


def _resolve_fk(model_name, csv_column, value):
    fk_map = FK_COLUMNS.get(model_name, {})
    if csv_column not in fk_map:
        return csv_column, value

    django_field, lookup_field, related_model = fk_map[csv_column]
    try:
        obj = related_model.objects.get(**{lookup_field: int(value)})
        return django_field, obj
    except related_model.DoesNotExist:
        raise ValueError(
            f"{related_model.__name__} with {lookup_field}='{value}' not found"
        )


def _get_model_field_names(model_name):
    model_class = MODEL_MAP[model_name]
    return {f.name for f in model_class._meta.get_fields() if hasattr(f, 'column')}


def _convert_row(model_name, row):
    converted = {}
    date_fields = DATE_FIELDS.get(model_name, [])
    decimal_fields = DECIMAL_FIELDS.get(model_name, [])
    integer_fields = INTEGER_FIELDS.get(model_name, [])
    fk_map = FK_COLUMNS.get(model_name, {})
    valid_fields = _get_model_field_names(model_name)

    for field, value in row.items():
        field = field.strip()
        value = value.strip() if value else ''

        if field in SKIP_FIELDS or not value:
            continue

        if field in fk_map:
            django_field, resolved = _resolve_fk(model_name, field, value)
            converted[django_field] = resolved
        elif field in date_fields:
            converted[field] = _parse_date(value)
        elif field in decimal_fields:
            converted[field] = _parse_decimal(value)
        elif field in integer_fields:
            converted[field] = int(value)
        elif field in valid_fields:
            converted[field] = value

    return converted


def import_csv(model_name, file_content):
    model_name = model_name.strip().lower()

    if model_name not in MODEL_MAP:
        raise ValueError(
            f"Unknown model '{model_name}'. "
            f"Available: {', '.join(MODEL_MAP.keys())}"
        )

    model_class = MODEL_MAP[model_name]

    decoded = file_content.decode('utf-8-sig')
    delimiter = _detect_delimiter(decoded)
    reader = csv.DictReader(io.StringIO(decoded), delimiter=delimiter)

    created = 0
    errors = []

    with transaction.atomic():
        for i, row in enumerate(reader, start=2):
            try:
                data = _convert_row(model_name, row)
                model_class.objects.create(**data)
                created += 1
            except Exception as e:
                errors.append({'row': i, 'error': str(e)})

        if errors and created == 0:
            raise ValueError(errors)

    return {
        'model': model_name,
        'created': created,
        'errors': errors,
    }


def import_all_csvs():
    if not CSV_FOLDER.exists():
        raise ValueError(
            f"CSV folder not found at '{CSV_FOLDER}'. "
            f"BASE_DIR='{settings.BASE_DIR}'"
        )

    results = []

    for filename in IMPORT_ORDER:
        csv_path = CSV_FOLDER / f'{filename}.csv'
        if not csv_path.exists():
            results.append({
                'file': f'{filename}.csv',
                'status': 'skipped',
                'reason': f'file not found at {csv_path}',
            })
            continue

        model_name = FILENAME_TO_MODEL[filename]
        try:
            content = csv_path.read_bytes()
            result = import_csv(model_name, content)
            results.append({
                'file': f'{filename}.csv',
                'status': 'ok',
                **result,
            })
        except Exception as e:
            results.append({
                'file': f'{filename}.csv',
                'status': 'error',
                'error': str(e),
            })

    return results
