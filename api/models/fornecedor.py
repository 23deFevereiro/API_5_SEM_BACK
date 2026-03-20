from django.db import models

class Fornecedor(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
        ('Bloqueado', 'Bloqueado'),
    ]

    codigo_fornecedor = models.CharField(max_length=20, unique=True)
    razao_social = models.CharField(max_length=150)
    nome_fantasia = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=20, unique=True)
    cidade = models.CharField(max_length=80)
    estado = models.CharField(max_length=2)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    condicao_pagamento = models.CharField(max_length=30)
    categoria_fornecedor = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    data_cadastro = models.DateField()