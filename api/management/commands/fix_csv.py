import shutil
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FOLDER = os.path.join(SCRIPT_DIR, 'original_documents')
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, 'corrected_documents')

STATUS_CONCLUIDO = 'Concluído'
STATUS_CONCLUIDA = 'Concluída'

def criar_pasta_saida():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"📁 Pasta criada: {OUTPUT_FOLDER}")

def salvar_csv(df, nome_arquivo):
    caminho = os.path.join(OUTPUT_FOLDER, nome_arquivo)
    df.to_csv(caminho, index=False, encoding='utf-8-sig')
    print(f"   ✅ Salvo: {nome_arquivo} ({len(df)} registros)")
    return caminho

def corrigir_inconsistencia_1(df_tempo, df_tarefas):
    print("\n📌 #1 - Corrigindo conflito de responsável por tarefa...")
    
    mapa_responsavel = dict(zip(df_tarefas['id'], df_tarefas['responsavel']))
    
    df_tempo_corrigido = df_tempo.copy()
    registros_alterados = 0
    
    for idx, row in df_tempo_corrigido.iterrows():
        tarefa_id = row['tarefa_id']
        if tarefa_id in mapa_responsavel:
            novo_responsavel = mapa_responsavel[tarefa_id]
            if row['usuario'] != novo_responsavel:
                df_tempo_corrigido.at[idx, 'usuario'] = novo_responsavel
                registros_alterados += 1
    
    print(f"   ✅ {registros_alterados} registros corrigidos")
    return df_tempo_corrigido

def corrigir_inconsistencia_2(df_projetos, df_programas):
    print("\n📌 #2 - Corrigindo status de projeto inconsistente com programa...")
    
    programas_concluidos = df_programas[df_programas['status'] == STATUS_CONCLUIDO]['id'].tolist()
    
    df_projetos_corrigido = df_projetos.copy()
    registros_alterados = 0
    
    for idx, row in df_projetos_corrigido.iterrows():
        programa_id = row['programa_id']
        if programa_id in programas_concluidos and row['status'] != STATUS_CONCLUIDO:
            df_projetos_corrigido.at[idx, 'status'] = STATUS_CONCLUIDO
            registros_alterados += 1
    
    print(f"   ✅ {registros_alterados} registros corrigidos")
    return df_projetos_corrigido

def corrigir_inconsistencia_3(df_tarefas, df_projetos):
    print("\n📌 #3 - Corrigindo status de tarefa inconsistente com projeto...")
    
    projetos_concluidos = df_projetos[df_projetos['status'] == STATUS_CONCLUIDO]['id'].tolist()
    
    df_tarefas_corrigido = df_tarefas.copy()
    registros_alterados = 0
    
    for idx, row in df_tarefas_corrigido.iterrows():
        projeto_id = row['projeto_id']
        if projeto_id in projetos_concluidos and row['status'] != STATUS_CONCLUIDA:
            df_tarefas_corrigido.at[idx, 'status'] = STATUS_CONCLUIDA
            registros_alterados += 1
    
    print(f"   ✅ {registros_alterados} registros corrigidos")
    return df_tarefas_corrigido

def _parsear_data_fim(data_fim):
    if pd.isna(data_fim):
        return None
    if isinstance(data_fim, str):
        try:
            return datetime.strptime(data_fim, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    return data_fim

def _determinar_novo_status(data_fim, data_atual):
    if data_fim and data_fim < data_atual:
        return STATUS_CONCLUIDA
    return 'Em andamento'

def corrigir_inconsistencia_4(df_tarefas, df_tempo):
    print("\n📌 #4 - Corrigindo tarefas em backlog com horas registradas...")
    
    horas_por_tarefa = df_tempo.groupby('tarefa_id')['horas_trabalhadas'].sum().reset_index()
    horas_por_tarefa.columns = ['tarefa_id', 'total_horas']
    
    tarefas_com_horas = set(horas_por_tarefa[horas_por_tarefa['total_horas'] > 0]['tarefa_id'].tolist())
    
    df_tarefas_corrigido = df_tarefas.copy()
    registros_alterados = 0
    data_atual = datetime.now().date()
    
    for idx, row in df_tarefas_corrigido.iterrows():
        tarefa_id = row['id']
        status_atual = row['status']
        
        if status_atual not in ['Não iniciada'] or tarefa_id not in tarefas_com_horas:
            continue
        
        data_fim = _parsear_data_fim(row['data_fim_prevista'])
        novo_status = _determinar_novo_status(data_fim, data_atual)
        df_tarefas_corrigido.at[idx, 'status'] = novo_status
        registros_alterados += 1
    
    print(f"   ✅ {registros_alterados} registros corrigidos")
    return df_tarefas_corrigido

def corrigir_programas_concluidos(df_programas, df_projetos, df_tarefas):
    print("\n📌 #5 - Aplicando correção em cascata (Programa -> Projeto -> Tarefa)...")
    
    programas_concluidos = df_programas[df_programas['status'] == STATUS_CONCLUIDO]['id'].tolist()
    
    projetos_corrigidos = 0
    for idx, row in df_projetos.iterrows():
        if row['programa_id'] in programas_concluidos and row['status'] != STATUS_CONCLUIDO:
            df_projetos.at[idx, 'status'] = STATUS_CONCLUIDO
            projetos_corrigidos += 1
    
    projetos_concluidos = df_projetos[df_projetos['status'] == STATUS_CONCLUIDO]['id'].tolist()
    tarefas_corrigidas = 0
    for idx, row in df_tarefas.iterrows():
        if row['projeto_id'] in projetos_concluidos and row['status'] != STATUS_CONCLUIDA:
            df_tarefas.at[idx, 'status'] = STATUS_CONCLUIDA
            tarefas_corrigidas += 1
    
    print(f"   ✅ Projetos corrigidos em cascata: {projetos_corrigidos}")
    print(f"   ✅ Tarefas corrigidas em cascata: {tarefas_corrigidas}")
    
    return df_projetos, df_tarefas

def main():
    print("=" * 70)
    print("🔧 SCRIPT DE CORREÇÃO DE INCONSISTÊNCIAS - DADOS DE PROJETOS")
    print("=" * 70)
    print(f"\n📂 Pasta de origem: {INPUT_FOLDER}")
    print(f"📂 Pasta de destino: {OUTPUT_FOLDER}")
    
    criar_pasta_saida()

    print("\n📖 Carregando arquivos CSV...")

    try:
        df_tempo = pd.read_csv(os.path.join(INPUT_FOLDER, 'tempo_tarefas.csv'))
        df_tarefas = pd.read_csv(os.path.join(INPUT_FOLDER, 'tarefas_projeto.csv'))
        df_projetos = pd.read_csv(os.path.join(INPUT_FOLDER, 'projetos.csv'))
        df_programas = pd.read_csv(os.path.join(INPUT_FOLDER, 'programas.csv'))
        
        print("   ✅ Todos os arquivos carregados com sucesso!")
        
    except FileNotFoundError as e:
        print(f"\n❌ Erro: Arquivo não encontrado - {e}")
        print("\n💡 Certifique-se de que:")
        print("   - A pasta 'original_documents' existe no diretório atual")
        print("   - Todos os arquivos CSV estão presentes")
        print("   - Os nomes dos arquivos estão corretos")
        sys.exit(1)
    
    df_tempo = corrigir_inconsistencia_1(df_tempo, df_tarefas)
    
    df_projetos = corrigir_inconsistencia_2(df_projetos, df_programas)
    
    df_tarefas = corrigir_inconsistencia_3(df_tarefas, df_projetos)
    
    df_tarefas = corrigir_inconsistencia_4(df_tarefas, df_tempo)
    
    df_projetos, df_tarefas = corrigir_programas_concluidos(df_programas, df_projetos, df_tarefas)
    
    print("\n💾 Salvando arquivos corrigidos...")
    
    salvar_csv(df_tempo, 'tempo_tarefas_corrigido.csv')
    salvar_csv(df_tarefas, 'tarefas_projeto_corrigido.csv')
    salvar_csv(df_projetos, 'projetos_corrigido.csv')

    print("\n📋 Copiando arquivos sem correções...")

    for nome in ['programas.csv', 'materiais.csv', 'fornecedores.csv', 'compras_projeto.csv', 'estoque_materiais_projeto.csv']:
        src = os.path.join(INPUT_FOLDER, nome)
        dst = os.path.join(OUTPUT_FOLDER, nome)
        shutil.copy2(src, dst)
        print(f"   ✅ Copiado: {nome}")

    for nome_origem, nome_destino in [
        ('empenho_materiais.csv',   'empenho_materiais_corrigido.csv'),
        ('solicitacoes_compra.csv', 'solicitacoes_compra_corrigido.csv'),
        ('pedidos_compra.csv',      'pedidos_compra_corrigido.csv'),
    ]:
        src = os.path.join(INPUT_FOLDER, nome_origem)
        dst = os.path.join(OUTPUT_FOLDER, nome_destino)
        shutil.copy2(src, dst)
        print(f"   ✅ Copiado: {nome_origem} → {nome_destino}")

    print("\n" + "=" * 70)
    print("✅ CORREÇÕES CONCLUÍDAS COM SUCESSO!")
    print("=" * 70)
    print(f"\n📁 Arquivos corrigidos salvos em: {OUTPUT_FOLDER}")
    print("\n📋 Resumo das correções aplicadas:")
    print("   #1 - Conflito de responsável por tarefa: corrigido")
    print("   #2 - Status de projeto inconsistente com programa: corrigido")
    print("   #3 - Status de tarefa inconsistente com projeto: corrigido")
    print("   #4 - Tarefas em backlog com horas registradas: corrigido")
    print("   #5 - Correção em cascata (Programa → Projeto → Tarefa): aplicada")
    
    print("\n🎯 Próximos passos:")
    print("   1. Validar os arquivos corrigidos na pasta 'corrected_documents'")
    print("   2. Executar o ETL para carregar os dados no banco")
    
    return 0

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Corrige inconsistências nos CSVs de origem e salva na pasta corrected_documents.'

    def handle(self, *args, **options):
        result = main()
        if result != 0:
            raise SystemExit(result)


if __name__ == "__main__":
    sys.exit(main())
