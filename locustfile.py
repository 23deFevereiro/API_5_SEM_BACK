"""
Teste de carga — API Dashboard
================================
Simula usuários navegando pelo dashboard: listam projetos/programas,
abrem detalhes e consultam dados de compras.

Uso rápido (rodando em outra máquina, apontando para a VM do backend):
    pip install locust
    locust -f locustfile.py --host=http://<IP-DA-VM-BACKEND>:8000

UI: http://localhost:8089

IDs alinhados com os seeds (seed_0006 carrega 3 programas, 100 projetos
e 100 materiais a partir dos CSVs em api/management/commands/corrected_documents).
Ajustar se o banco de teste tiver outro conjunto.
"""

import random

from locust import HttpUser, between, task

PROGRAMA_IDS = [1, 2, 3]
PROJETO_IDS = list(range(1, 101))
MATERIAL_IDS = list(range(1, 101))


class UsuarioDashboard(HttpUser):
    """
    Simula um analista navegando pelo dashboard.
    Espera entre 2 e 5 segundos entre cada ação — comportamento humano realista.
    """
    wait_time = between(2, 5)

    # ── Visão geral (página inicial — mais acessada) ──────────────────────────

    @task(5)
    def overview_projetos(self):
        """Tela inicial de projetos — alta frequência."""
        self.client.get("/api/projetos-overview", name="/api/projetos-overview")

    @task(4)
    def listar_projetos(self):
        self.client.get("/api/projetos/", name="/api/projetos/")

    @task(3)
    def listar_programas(self):
        self.client.get("/api/programas/", name="/api/programas/")

    # ── Burnup (gráficos globais — acessados com frequência média) ────────────

    @task(3)
    def burnup_horas_projetos(self):
        self.client.get("/api/projetos/burnup-horas/", name="/api/projetos/burnup-horas/")

    @task(2)
    def burnup_horas_programas(self):
        self.client.get("/api/programas-burnup-horas/", name="/api/programas-burnup-horas/")

    @task(2)
    def burnup_custo_programas(self):
        self.client.get("/api/programas-burnup-custo/", name="/api/programas-burnup-custo/")

    # ── Detalhes de projeto (usuário abre um projeto específico) ──────────────

    @task(3)
    def resumo_projeto(self):
        pid = random.choice(PROJETO_IDS)
        self.client.get(f"/api/projetos/{pid}/resumo/", name="/api/projetos/[id]/resumo/")

    @task(2)
    def materiais_projeto(self):
        pid = random.choice(PROJETO_IDS)
        self.client.get(f"/api/projetos/{pid}/materiais/", name="/api/projetos/[id]/materiais/")

    @task(2)
    def horas_por_funcionario(self):
        pid = random.choice(PROJETO_IDS)
        self.client.get(f"/api/projetos/{pid}/horas-por-funcionario/", name="/api/projetos/[id]/horas-por-funcionario/")

    @task(2)
    def funcionarios_projeto(self):
        pid = random.choice(PROJETO_IDS)
        self.client.get(f"/api/projetos/{pid}/funcionarios/", name="/api/projetos/[id]/funcionarios/")

    @task(1)
    def nomes_funcionarios(self):
        pid = random.choice(PROJETO_IDS)
        self.client.get(f"/api/projetos/{pid}/nomes-funcionarios/", name="/api/projetos/[id]/nomes-funcionarios/")

    @task(1)
    def materiais_disponiveis(self):
        pid = random.choice(PROJETO_IDS)
        self.client.get(f"/api/projetos/{pid}/materiais-disponiveis/", name="/api/projetos/[id]/materiais-disponiveis/")

    # ── Detalhes de programa ──────────────────────────────────────────────────

    @task(2)
    def resumo_programa(self):
        pgid = random.choice(PROGRAMA_IDS)
        self.client.get(f"/api/programas/{pgid}/resumo/", name="/api/programas/[id]/resumo/")

    @task(2)
    def tabela_projetos_programa(self):
        pgid = random.choice(PROGRAMA_IDS)
        self.client.get(f"/api/programas/{pgid}/tabela-projetos/", name="/api/programas/[id]/tabela-projetos/")

    @task(1)
    def distribuicao_status(self):
        pgid = random.choice(PROGRAMA_IDS)
        self.client.get(f"/api/programas/{pgid}/distribuicao-status/", name="/api/programas/[id]/distribuicao-status/")

    @task(1)
    def horas_por_projeto(self):
        pgid = random.choice(PROGRAMA_IDS)
        self.client.get(f"/api/programas/{pgid}/horas-por-projeto/", name="/api/programas/[id]/horas-por-projeto/")

    # ── Compras (módulo consultado com menos frequência) ─────────────────────

    @task(2)
    def compras_alertas(self):
        """Alertas de estoque — consultado com frequência."""
        self.client.get("/api/compras/alertas/", name="/api/compras/alertas/")

    @task(1)
    def compras_materiais(self):
        self.client.get("/api/compras/materiais/", name="/api/compras/materiais/")

    @task(1)
    def compras_lead_time(self):
        mid = random.choice(MATERIAL_IDS)
        self.client.get(
            "/api/compras/lead-time/",
            params={"material_id": mid},
            name="/api/compras/lead-time/",
        )

    @task(1)
    def compras_estoque_tabela(self):
        self.client.get("/api/compras/estoque-tabela/", name="/api/compras/estoque-tabela/")
