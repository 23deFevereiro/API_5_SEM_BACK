"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from .views import (
    compras_view,
    funcionario_view,
    horas_view,
    programa_view,
    projeto_view,
)

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path(
        "api/projetos-overview",
        projeto_view.get_overview_projetos,
        name="projetos_overview",
    ),
    path("api/projetos/", projeto_view.listar_projetos_view, name="listar_projetos"),
    path(
        "api/projetos/<int:projeto_id>/resumo/",
        projeto_view.get_resumo_projeto_view,
        name="resumo_projeto",
    ),
    path(
        "api/projetos/<int:projeto_id>/materiais/",
        projeto_view.get_materiais_projeto_view,
        name="materiais_projeto",
    ),
    path(
        "api/projetos/<int:projeto_id>/horas-por-funcionario/",
        horas_view.get_horas_por_funcionario_view,
        name="horas_por_funcionario",
    ),
    path(
        "api/projetos/burnup-horas/",
        horas_view.get_burnup_horas_projetos_view,
        name="burnup_horas_projetos",
    ),
    path(
        "api/projetos/<int:projeto_id>/funcionarios/",
        funcionario_view.get_funcionarios_projeto_view,
        name="funcionarios_projeto",
    ),
    path(
        "api/projetos/<int:projeto_id>/nomes-funcionarios/",
        horas_view.get_nomes_funcionarios_view,
        name="nomes_funcionarios_projeto",
    ),
    path(
        "api/projetos/<int:projeto_id>/materiais-disponiveis/",
        projeto_view.get_materiais_disponiveis_view,
        name="materiais_disponiveis_projeto",
    ),
    path(
        "api/programas/", programa_view.listar_programas_view, name="listar_programas"
    ),
    path(
        "api/programas/<int:programa_id>/resumo/",
        programa_view.get_resumo_programa_view,
        name="resumo_programa",
    ),
    path(
        "api/programas/<int:programa_id>/distribuicao-status/",
        programa_view.get_distribuicao_status_view,
        name="distribuicao_status",
    ),
    path(
        "api/programas-burnup-horas/",
        programa_view.get_burnup_horas_programas_view,
        name="programas_burnup_horas",
    ),
    path(
        "api/programas-burnup-custo/",
        programa_view.get_burnup_custo_programas_view,
        name="programas_burnup_custo",
    ),
    path(
        "api/programas/<int:programa_id>/tabela-projetos/",
        programa_view.get_tabela_projetos_view,
        name="tabela_projetos",
    ),
    path(
        "api/programas/<int:programa_id>/horas-por-projeto/",
        programa_view.get_horas_por_projeto_view,
        name="horas_por_projeto",
    ),
    path(
        "api/compras/materiais/",
        compras_view.listar_materiais_compras_view,
        name="compras_materiais",
    ),
    path(
        "api/compras/lead-time/",
        compras_view.get_lead_time_view,
        name="compras_lead_time",
    ),
    path("api/compras/alertas/", compras_view.get_alertas_view, name="compras_alertas"),
]
