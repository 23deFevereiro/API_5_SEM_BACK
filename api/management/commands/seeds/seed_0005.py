from django.core.management.base import BaseCommand
from api.management.commands.seeds import seed_0004

MIGRATION_REF = '0005'


def run():
    seed_0004.run()


class Command(BaseCommand):
    help = f'Seed {MIGRATION_REF}: popula as tabelas do Star Model (dimensões e fatos)'

    def handle(self, *args, **options):
        run()
