import importlib
from pathlib import Path
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

CORRECTED_DOCUMENTS_DIR = Path(__file__).parent / 'corrected_documents'

MIGRATION_WARNINGS = {
    '0003': (
        '\n' + '!' * 70 + '\n'
        '  ⚠️  AVISO DE INCOMPATIBILIDADE\n\n'
        '  A seed 0003 popula o modelo RELACIONAL:\n'
        '    programa, projeto, tarefa, tempo_tarefa, fornecedor, material,\n'
        '    pedido_compra, solicitacao_compra, empenho_material, estoque_material_projeto\n\n'
        '  A partir da migration 0004 o sistema utiliza o modelo ESTRELA:\n'
        '    dim_programa, dim_projeto, dim_tarefa, dim_material, dim_fornecedor,\n'
        '    dim_funcionario, dim_status_pedido, dim_tempo,\n'
        '    fato_horas, fato_materiais, fato_compras, fato_estoque\n\n'
        '  ➡️  A aplicação atual (views, services, APIs) NÃO É COMPATÍVEL com\n'
        '      o banco gerado por esta seed. Use apenas para testes isolados\n'
        '      do modelo relacional ou para fins de desenvolvimento da sprint 3.\n'
        + '!' * 70
    ),
}


def ensure_corrected_documents():
    if not CORRECTED_DOCUMENTS_DIR.exists() or not any(CORRECTED_DOCUMENTS_DIR.glob('*.csv')):
        print('   ⚠️  Arquivos de corrected_documents não encontrados. Executando fix_csv...')
        call_command('fix_csv')
        print('   ✅ fix_csv concluído.')


def get_latest_applied_migration(app_label='api'):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM django_migrations
            WHERE app = %s
            ORDER BY id DESC
            LIMIT 1
        """, [app_label])
        row = cursor.fetchone()
        if not row:
            raise CommandError(f"Nenhuma migration encontrada para o app '{app_label}'.")
        return row[0].split('_')[0]


def load_seed(migration_number):
    module_name = f'api.management.commands.seeds.seed_{migration_number}'
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        raise CommandError(
            f"Seed não encontrado: '{module_name}'.\n"
            f"Crie o arquivo seed_{migration_number}.py em api/management/commands/seeds."
        )
    if not hasattr(module, 'run'):
        raise CommandError(
            f"O arquivo seed_{migration_number}.py não possui a função 'run'."
        )
    return module


class Command(BaseCommand):
    help = (
        'Popula o banco de dados executando o seed correspondente à migration atual. '
        'O seed é selecionado automaticamente com base na última migration aplicada.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--migration',
            type=str,
            help='Força a execução de um seed específico pelo número da migration (ex: 0004).',
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write('🚀 dev_db - Orquestrador de Seed do Banco de Dados')
        self.stdout.write('=' * 70)

        migration_number = options.get('migration')

        self.stdout.write('\n🗂️  Verificando arquivos de corrected_documents...')
        ensure_corrected_documents()

        if migration_number:
            self.stdout.write(f'\n🔧 Migration forçada via argumento: {migration_number}')
            warning = MIGRATION_WARNINGS.get(migration_number)
            if warning:
                self.stdout.write(self.style.WARNING(warning))
        else:
            self.stdout.write('\n🔍 Detectando última migration aplicada...')
            migration_number = get_latest_applied_migration()
            self.stdout.write(f'   ✅ Migration detectada: {migration_number}')

        self.stdout.write(f'\n📂 Carregando seed_{migration_number}.py...')
        seed_module = load_seed(migration_number)

        try:
            seed_module.run()
        except Exception as e:
            raise CommandError(f'Erro ao executar seed_{migration_number}: {e}')

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ Banco de dados populado com sucesso!'))
        self.stdout.write('=' * 70)
