from django.db import models


class ProgramaEmpresa(models.Model):
    codigo_programa   = models.CharField(max_length=50, unique=True)
    nome_programa     = models.CharField(max_length=255)
    gerente_programa  = models.CharField(max_length=255)
    gerente_tecnico   = models.CharField(max_length=255, null=True, blank=True)
    data_inicio       = models.DateField(null=True, blank=True)
    data_fim_prevista = models.DateField(null=True, blank=True)
    status            = models.CharField(max_length=50)

    class Meta:
        app_label = "api"
        db_table  = "programas_empresa"

    def __str__(self):
        return self.codigo_programa


class ProjetoPrograma(models.Model):
    codigo_projeto    = models.CharField(max_length=50, unique=True)
    nome_projeto      = models.CharField(max_length=255)
    programa          = models.ForeignKey(ProgramaEmpresa, on_delete=models.PROTECT, related_name="projetos")
    responsavel       = models.CharField(max_length=255)
    custo_hora        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_inicio       = models.DateField(null=True, blank=True)
    data_fim_prevista = models.DateField(null=True, blank=True)
    status            = models.CharField(max_length=50)

    class Meta:
        app_label = "api"
        db_table  = "projetos_programas"

    def __str__(self):
        return self.codigo_projeto


class TarefaProjeto(models.Model):
    codigo_tarefa     = models.CharField(max_length=50, unique=True)
    projeto           = models.ForeignKey(ProjetoPrograma, on_delete=models.PROTECT, related_name="tarefas")
    titulo            = models.CharField(max_length=255)
    responsavel       = models.CharField(max_length=255)
    estimativa_horas  = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    data_inicio       = models.DateField(null=True, blank=True)
    data_fim_prevista = models.DateField(null=True, blank=True)
    status            = models.CharField(max_length=50)

    class Meta:
        app_label = "api"
        db_table  = "tarefas_projeto"

    def __str__(self):
        return self.codigo_tarefa


class TempoTarefa(models.Model):
    tarefa            = models.ForeignKey(TarefaProjeto, on_delete=models.PROTECT, related_name="registros_tempo")
    usuario           = models.CharField(max_length=255)
    data              = models.DateField()
    horas_trabalhadas = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        app_label       = "api"
        db_table        = "tempo_tarefas"
        unique_together = ("tarefa", "usuario", "data")

    def __str__(self):
        return f"{self.tarefa} | {self.usuario} | {self.data}"


class Fornecedor(models.Model):
    codigo_fornecedor = models.CharField(max_length=50, unique=True)
    razao_social      = models.CharField(max_length=255)
    cidade            = models.CharField(max_length=100)
    estado            = models.CharField(max_length=2)
    categoria         = models.CharField(max_length=100)
    status            = models.CharField(max_length=50)

    class Meta:
        app_label = "api"
        db_table  = "fornecedores"

    def __str__(self):
        return self.codigo_fornecedor


class Material(models.Model):
    codigo_material = models.CharField(max_length=50, unique=True)
    descricao       = models.CharField(max_length=255)
    categoria       = models.CharField(max_length=100)
    fabricante      = models.CharField(max_length=255)
    custo_estimado  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status          = models.CharField(max_length=50)
    lead_time       = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = "api"
        db_table  = "materiais"

    def __str__(self):
        return self.codigo_material


class SolicitacaoCompra(models.Model):
    numero_solicitacao = models.CharField(max_length=50, unique=True)
    projeto            = models.ForeignKey(ProjetoPrograma, on_delete=models.PROTECT, related_name="solicitacoes")
    material           = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="solicitacoes")
    quantidade         = models.IntegerField(null=True, blank=True)
    data_solicitacao   = models.DateField(null=True, blank=True)
    prioridade         = models.CharField(max_length=50)
    status             = models.CharField(max_length=50)

    class Meta:
        app_label = "api"
        db_table  = "solicitacoes_compra"

    def __str__(self):
        return self.numero_solicitacao


class PedidoCompra(models.Model):
    numero_pedido         = models.CharField(max_length=50, unique=True)
    solicitacao           = models.ForeignKey(SolicitacaoCompra, on_delete=models.PROTECT, related_name="pedidos")
    fornecedor            = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, related_name="pedidos")
    data_pedido           = models.DateField(null=True, blank=True)
    data_previsao_entrega = models.DateField(null=True, blank=True)
    valor_total           = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    status                = models.CharField(max_length=50)

    class Meta:
        app_label = "api"
        db_table  = "pedidos_compra"

    def __str__(self):
        return self.numero_pedido


class CompraProjeto(models.Model):
    projeto       = models.ForeignKey(ProjetoPrograma, on_delete=models.PROTECT, related_name="compras")
    pedido        = models.ForeignKey(PedidoCompra, on_delete=models.PROTECT, related_name="compras_projeto")
    valor_alocado = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    class Meta:
        app_label       = "api"
        db_table        = "compras_projeto"
        unique_together = ("projeto", "pedido")

    def __str__(self):
        return f"{self.projeto} | {self.pedido}"


class EmpenhoMaterial(models.Model):
    projeto              = models.ForeignKey(ProjetoPrograma, on_delete=models.PROTECT, related_name="empenhos")
    material             = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="empenhos")
    quantidade_empenhada = models.IntegerField(null=True, blank=True)
    data_empenho         = models.DateField(null=True, blank=True)

    class Meta:
        app_label       = "api"
        db_table        = "empenho_materiais"
        unique_together = ("projeto", "material")

    def __str__(self):
        return f"{self.projeto} | {self.material}"


class EstoqueMaterialProjeto(models.Model):
    projeto     = models.ForeignKey(ProjetoPrograma, on_delete=models.PROTECT, related_name="estoques")
    material    = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="estoques")
    quantidade  = models.IntegerField(null=True, blank=True)
    localizacao = models.CharField(max_length=255)

    class Meta:
        app_label       = "api"
        db_table        = "estoque_materiais_projeto"
        unique_together = ("projeto", "material")

    def __str__(self):
        return f"{self.projeto} | {self.material}"

from .demo import Demo
from .programa import Programa
from .fornecedor import Fornecedor
from .material import Material
from .projeto import Projeto
from .tarefa import Tarefa
from .tempo_tarefa import TempoTarefa
from .estoque_material_projeto import EstoqueMaterialProjeto
from .empenho_material import EmpenhoMaterial
from .pedido_compra import PedidoCompra
from .solicitacao_compra import SolicitacaoCompra
from .compras_projeto import ComprasProjeto
