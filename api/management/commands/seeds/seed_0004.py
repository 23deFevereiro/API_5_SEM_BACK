from django.core.management.base import BaseCommand

MIGRATION_REF = "0004"


def run():
    from . import seed_0003, seed_0005

    print(f"\n📦 Seed {MIGRATION_REF} - Carregando modelo relacional (seed 0003)...")
    seed_0003.run()
    print(
        f"\n📦 Seed {MIGRATION_REF} - Carregando dimensões e fatos do Star Model (seed 0005)..."
    )
    seed_0005.run()


class Command(BaseCommand):
    help = f"Seed {MIGRATION_REF}: popula modelo relacional e Star Model"

    def handle(self, *args, **options):
        run()
