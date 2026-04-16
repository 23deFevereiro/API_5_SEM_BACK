import importlib
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


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
            f"O arquivo seed_{migration_number}.py não possui a função 'run()'."
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

        if migration_number:
            self.stdout.write(f'\n🔧 Migration forçada via argumento: {migration_number}')
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
