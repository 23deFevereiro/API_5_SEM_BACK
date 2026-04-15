DROP TABLE IF EXISTS fato_estoque CASCADE;
DROP TABLE IF EXISTS fato_compras CASCADE;
DROP TABLE IF EXISTS fato_materiais CASCADE;
DROP TABLE IF EXISTS fato_horas CASCADE;
DROP TABLE IF EXISTS dim_tempo CASCADE;
DROP TABLE IF EXISTS dim_status_pedido CASCADE;
DROP TABLE IF EXISTS dim_funcionario CASCADE;
DROP TABLE IF EXISTS dim_fornecedor CASCADE;
DROP TABLE IF EXISTS dim_material CASCADE;
DROP TABLE IF EXISTS dim_tarefa CASCADE;
DROP TABLE IF EXISTS dim_projeto CASCADE;
DROP TABLE IF EXISTS dim_programa CASCADE;

CREATE TABLE IF NOT EXISTS dim_programa (
    id INTEGER PRIMARY KEY,
    codigo_programa VARCHAR(20) NOT NULL UNIQUE,
    nome_programa VARCHAR(100) NOT NULL,
    gerente_programa VARCHAR(100),
    data_inicio DATE,
    data_fim_prevista DATE,
    status VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS dim_projeto (
    id INTEGER PRIMARY KEY,
    codigo_projeto VARCHAR(20) NOT NULL UNIQUE,
    nome_projeto VARCHAR(100) NOT NULL,
    programa_id INTEGER REFERENCES dim_programa(id),
    responsavel VARCHAR(100),
    custo_hora DECIMAL(10,2),
    status VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS dim_tarefa (
    id INTEGER PRIMARY KEY,
    codigo_tarefa VARCHAR(20) NOT NULL UNIQUE,
    projeto_id INTEGER REFERENCES dim_projeto(id),
    titulo VARCHAR(200) NOT NULL,
    responsavel VARCHAR(100),
    horas_estimadas DECIMAL(10,2),
    status VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS dim_material (
    id INTEGER PRIMARY KEY,
    codigo_material VARCHAR(20) NOT NULL UNIQUE,
    descricao VARCHAR(200) NOT NULL,
    categoria VARCHAR(50),
    fabricante VARCHAR(100),
    custo_estimado DECIMAL(10,2),
    status VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS dim_fornecedor (
    id INTEGER PRIMARY KEY,
    codigo_fornecedor VARCHAR(20) NOT NULL UNIQUE,
    razao_social VARCHAR(100) NOT NULL,
    cidade VARCHAR(50),
    estado VARCHAR(2),
    categoria VARCHAR(50),
    status VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS dim_funcionario (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_status_pedido (
    id SERIAL PRIMARY KEY,
    nome_status VARCHAR(30) NOT NULL UNIQUE,
    categoria VARCHAR(20) NOT NULL,
    ordem_prioridade INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dim_tempo (
    id INTEGER PRIMARY KEY,
    data DATE NOT NULL UNIQUE,
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    semestre INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fato_horas (
    id SERIAL PRIMARY KEY,
    tempo_id INTEGER NOT NULL REFERENCES dim_tempo(id),
    projeto_id INTEGER NOT NULL REFERENCES dim_projeto(id),
    programa_id INTEGER NOT NULL REFERENCES dim_programa(id),
    tarefa_id INTEGER NOT NULL REFERENCES dim_tarefa(id),
    funcionario_id INTEGER NOT NULL REFERENCES dim_funcionario(id),
    horas_trabalhadas DECIMAL(10,2) DEFAULT 0,
    custo_horas DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fato_materiais (
    id SERIAL PRIMARY KEY,
    tempo_id INTEGER NOT NULL REFERENCES dim_tempo(id),
    projeto_id INTEGER NOT NULL REFERENCES dim_projeto(id),
    programa_id INTEGER NOT NULL REFERENCES dim_programa(id),
    material_id INTEGER NOT NULL REFERENCES dim_material(id),
    fornecedor_id INTEGER REFERENCES dim_fornecedor(id),
    quantidade_empenhada INTEGER DEFAULT 0,
    custo_materiais DECIMAL(10,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fato_compras (
    id SERIAL PRIMARY KEY,
    tempo_id INTEGER NOT NULL REFERENCES dim_tempo(id),
    projeto_id INTEGER REFERENCES dim_projeto(id),
    material_id INTEGER NOT NULL REFERENCES dim_material(id),
    fornecedor_id INTEGER NOT NULL REFERENCES dim_fornecedor(id),
    status_id INTEGER NOT NULL REFERENCES dim_status_pedido(id),
    quantidade_solicitada INTEGER DEFAULT 0,
    quantidade_entregue INTEGER DEFAULT 0,
    valor_alocado DECIMAL(10,2) DEFAULT 0,
    valor_total DECIMAL(10,2) DEFAULT 0,
    lead_time INTEGER,
    data_previsao_entrega DATE
);

CREATE TABLE IF NOT EXISTS fato_estoque (
    id SERIAL PRIMARY KEY,
    tempo_id INTEGER NOT NULL REFERENCES dim_tempo(id),
    material_id INTEGER NOT NULL REFERENCES dim_material(id),
    projeto_id INTEGER NOT NULL REFERENCES dim_projeto(id),
    quantidade_estoque INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_fato_horas_tempo ON fato_horas(tempo_id);
CREATE INDEX IF NOT EXISTS idx_fato_horas_projeto ON fato_horas(projeto_id);
CREATE INDEX IF NOT EXISTS idx_fato_horas_tarefa ON fato_horas(tarefa_id);
CREATE INDEX IF NOT EXISTS idx_fato_materiais_tempo ON fato_materiais(tempo_id);
CREATE INDEX IF NOT EXISTS idx_fato_materiais_material ON fato_materiais(material_id);
CREATE INDEX IF NOT EXISTS idx_fato_compras_tempo ON fato_compras(tempo_id);
CREATE INDEX IF NOT EXISTS idx_fato_compras_material ON fato_compras(material_id);
CREATE INDEX IF NOT EXISTS idx_fato_estoque_material ON fato_estoque(material_id);
