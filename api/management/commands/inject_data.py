import os
from django.core.management.base import BaseCommand
from pathlib import Path

from ...services.csv_import_svc import import_all_csvs

from django.conf import settings

FILE_MODEL_MAP = {
    "compras_projeto": "compras_projeto",
    "empenho_materiais": "empenho_material",
    "estoque_materiais_projeto": "estoque_material_projeto",
    "fornecedores": "fornecedor",
    "materiais": "material",
    "pedidos_compra": "pedido_compra",
    "programas": "programa",
    "projetos": "projeto",
    "solicitacoes_compra": "solicitacao_compra",
    "tarefas_projeto": "tarefa",
    "tempo_tarefas": "tempo_tarefa",
}

class Command(BaseCommand):
    def handle(self, *args, **options):
        import_all_csvs()