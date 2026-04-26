import pandas as pd
import psycopg2
import os
from pathlib import Path
from django.core.management.base import BaseCommand


DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'database'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}

MIGRATION_REF = '0004'
CSV_DIR = Path(__file__).parent.parent / 'corrected_documents'


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def _none(val):
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return val


def run():
    from . import seed_0003, seed_0005
    print(f"\n📦 Seed {MIGRATION_REF} - Carregando modelo relacional (seed 0003)...")
    seed_0003.run()
    print(f"\n📦 Seed {MIGRATION_REF} - Carregando dimensões e fatos do Star Model (seed 0005)...")
    seed_0005.run()


class Command(BaseCommand):
    help = f'Seed {MIGRATION_REF}: popula modelo relacional e Star Model'

    def handle(self, *args, **options):
        run()



class Command(BaseCommand):
    help = f'Seed {MIGRATION_REF}: popula as tabelas do Star Model (dimensões e fatos)'

    def handle(self, *args, **options):
        run()
