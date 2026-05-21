# Deploy — Arquitetura e Provisionamento

Documento técnico de referência para o time de TI responsável pelo deploy.
Cobre a arquitetura proposta, dimensionamento e os pontos de configuração.
Não cobre instalação básica de Postgres, Linux ou de um servidor web.

> Passo a passo prático de instalação está em [`setup.md`](setup.md).

---

## 1. Arquitetura

### 1.1 Topologia

```
                  Internet / rede corporativa
                              │
                              ▼ 80
        ┌──────────────────────────────────────────┐
        │   VM única                               │
        │                                          │
        │   ┌────────────────────────────────┐     │
        │   │ Nginx (reverse proxy + TLS)    │     │
        │   │ Frontend Vite (estático)       │     │
        │   └─────────────┬──────────────────┘     │
        │                 │ 127.0.0.1:8000         │
        │   ┌─────────────▼──────────────────┐     │
        │   │ Django + Gunicorn (loopback)   │     │
        │   └────────────────────────────────┘     │
        │   IP: <APP_IP>                           │
        └──────────────────────────────────────────┘
                              │ 5432
                              ▼
        ┌──────────────────────────────────────────┐
        │   PostgreSQL 18 (provisionado pelo TI)   │
        │   IP: <POSTGRES_HOST>                    │
        └──────────────────────────────────────────┘
```

### 1.2 Decisões arquiteturais

- **Aplicação inteira em uma VM:** nginx, frontend estático e backend
  compartilham recursos. Pro porte do projeto (até 200 usuários
  simultâneos no pico), separar em duas VMs traz mais overhead
  operacional que ganho real.
- **Backend em loopback:** o Gunicorn escuta apenas em `127.0.0.1:8000`.
  Só o nginx — que roda na mesma VM — consegue alcançá-lo. O serviço
  Django **nunca fica exposto à rede**, mesmo se o firewall da VM
  cair ou for mal configurado.
- **Frontend como estático servido pelo nginx:** o build do Vite gera
  apenas HTML/CSS/JS, sem runtime no servidor. Custo de CPU/RAM
  desprezível.
- **Postgres externo:** mantido na infraestrutura pré-existente do
  cliente. A aplicação só consome.

---

## 2. Dimensionamento

### 2.1 Recursos da VM

|   Período   | vCPUs | RAM  | Disco |
|-------------|-------|------|-------|
| Mês 1 ao 12 | **1** | 2 GB | 20 GB |
| Mês 13+     | **4** | 2 GB | 20 GB |

> RAM não é gargalo. O ponto de pressão é CPU.

### 2.2 Justificativa do upgrade no mês 12

Os testes de carga mostraram:

|        Cenário         | RPS  |  p50  |    p95   | Falhas |
|------------------------|------|-------|----------|--------|
|  50 usuários · 1 vCPU  | 8,6  | 2,2 s |  3,6 s   |   0    |
| 200 usuários · 1 vCPU  | 16,0 | 8,6 s | **11 s** |   0    |
| 200 usuários · 4 vCPUs | 32,5 | 2,4 s |  4,0 s   |   0    |

- **1 vCPU** atende a carga estimada até o mês 12 (~50 usuários
  simultâneos) com latência aceitável.
- A partir do mês 13, com a carga crescendo em direção aos 200
  usuários do pico do mês 18, 1 vCPU vira gargalo: p95 sobe para
  11 s, inviabilizando o uso.
- **Provisionar 4 vCPUs antes do mês 13** restabelece a latência
  ao patamar de uso normal mesmo no pico, com margem de crescimento.

A justificativa visual está em
[`loadtests/apresentacao.html`](../loadtests/index.html) e os
dados brutos em [`loadtests/`](../loadtests/).

### 2.3 O que NÃO precisa mudar no mês 12

- **RAM:** 2 GB seguem suficientes.
- **Postgres:** o teste mostrou no máximo 4 conexões ativas simultâneas
  no pico — muito abaixo de qualquer limite padrão.
- **Nginx:** desprezível mesmo no pico.

---

## 3. Comunicação

| Origem | Destino | Porta | Protocolo | Notas |
|---|---|---|---|---|
| Internet | VM | 80, 443 | HTTP/HTTPS | Nginx redireciona 80 → 443 |
| Nginx | Gunicorn | 8000 | HTTP (loopback) | Não exposto na rede |
| VM | Postgres | 5432 | TCP | Apenas pela rede privada |
| Admin/TI | VM | 22 | SSH | Restringir a rede de gestão |

**Regras de firewall a aplicar na VM:**

- Aceita 80/443 da rede pública (ou apenas corporativa, conforme o caso).
- Aceita 22 apenas da rede de gestão.
- Tudo mais negado.

**No Postgres:** aceitar 5432 apenas do IP da VM (`pg_hba.conf` +
firewall do servidor de banco).

---

## 4. Provisionamento (resumo)

O detalhe operacional está em [`setup.md`](setup.md). Em alto nível:

1. **VM Linux** com os recursos da tabela 2.1.
2. **Stack instalado:** Python 3.11+, nginx, postgresql-client.
3. **Backend** em `<BACKEND_PATH>` com venv, deps de `requirements.txt`
   e `.env` (ver seção 5).
4. **Frontend** com build do Vite (`npm run build`, fora da VM) e o
   `dist/` enviado para `/var/www/<APP_NAME>/`.
5. **Nginx** com site configurado: estático em `/` e proxy `/api/`
   para `127.0.0.1:8000`.
6. **Gunicorn** rodando como serviço `systemd`, em `127.0.0.1:8000`.

---

## 5. Variáveis de ambiente do backend

Arquivo `<BACKEND_PATH>/.env`:

```env
# Banco
POSTGRES_DB=<DB_NAME>
POSTGRES_USER=<DB_USER>
POSTGRES_PASSWORD=<DB_PASSWORD>
POSTGRES_HOST=<POSTGRES_HOST>
POSTGRES_PORT=<POSTGRES_PORT>

# Django
SECRET_KEY=<RANDOM_SECRET_KEY>
DEBUG=False
ALLOWED_HOSTS=<APP_IP>,<DOMAIN>
```

Pontos críticos:

- **`SECRET_KEY`:** gerar uma chave aleatória forte (50+ caracteres).
- **`DEBUG=False`:** obrigatório em produção. Com `DEBUG=True`, o
  Django acumula histórico de todas as queries em memória, causando
  vazamento progressivo e timeout sob carga.
- **`ALLOWED_HOSTS`:** incluir IP da VM e o domínio. Aceita
  vírgula-separado.

---

## 6. Gunicorn como serviço

Arquivo `/etc/systemd/system/<APP_NAME>-backend.service`:

```ini
[Unit]
Description=<APP_NAME> backend (Gunicorn)
After=network.target

[Service]
Type=simple
User=<APP_USER>
WorkingDirectory=<BACKEND_PATH>
EnvironmentFile=<BACKEND_PATH>/.env
ExecStart=<BACKEND_PATH>/.venv/bin/gunicorn api.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers <WORKERS> \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Onde `<WORKERS> = 2 × vCPUs + 1`:

| vCPUs | `<WORKERS>` |
|---|---|
| 1 (mês 1 ao 12) | 3 |
| 4 (mês 13+) | 9 |

Logs ficam disponíveis via:

```bash
journalctl -u <APP_NAME>-backend -f
```

---

## 7. Procedimento de upgrade para 4 vCPUs

1. Janela curta de manutenção (tipicamente < 2 min).
2. `sudo systemctl stop <APP_NAME>-backend`.
3. Desligar a VM e aumentar para 4 vCPUs no hypervisor.
4. Religar a VM.
5. Ajustar `--workers` para `9` no arquivo systemd e
   `sudo systemctl daemon-reload`.
6. `sudo systemctl start <APP_NAME>-backend`.
7. Smoke test (`curl https://<DOMAIN>/api/projetos-overview`) antes
   de reabrir tráfego.

Critérios para acionar o upgrade antes do prazo:

- p95 ultrapassando **5 segundos** de forma sustentada.
- Picos de CPU em **100%** por mais de 30 s contínuos.

---

## 8. Placeholders a preencher

| Placeholder | O que é | Exemplo |
|---|---|---|
| `<APP_IP>` | IP da VM na rede privada | `10.0.0.20` |
| `<DOMAIN>` | Domínio público | `lunae.cliente.com` |
| `<APP_NAME>` | Identificador curto | `lunae` |
| `<APP_USER>` | Usuário Linux que roda a aplicação | `lunae` |
| `<BACKEND_PATH>` | Diretório do backend na VM | `/opt/lunae/backend` |
| `<POSTGRES_HOST>` | Host/IP do Postgres | `10.0.0.30` |
| `<POSTGRES_PORT>` | Porta do Postgres | `5432` |
| `<DB_NAME>` | Nome do banco | `lunae` |
| `<DB_USER>` | Usuário do banco | `lunae` |
| `<DB_PASSWORD>` | Senha do banco | _(gerada pelo TI)_ |
| `<RANDOM_SECRET_KEY>` | Chave Django (50+ caracteres aleatórios) | _(gerada pelo TI)_ |
| `<SSL_CERT_PATH>` | Caminho do certificado TLS | `/etc/letsencrypt/live/<DOMAIN>/fullchain.pem` |
| `<SSL_KEY_PATH>` | Caminho da chave privada | `/etc/letsencrypt/live/<DOMAIN>/privkey.pem` |
| `<WORKERS>` | Nº de workers Gunicorn | `3` (1 vCPU) ou `9` (4 vCPUs) |

---

## 9. Verificações pós-deploy

1. Backend responde no loopback (na própria VM):
   ```bash
   curl http://127.0.0.1:8000/api/projetos-overview
   ```
2. Nginx responde pela rede pública:
   ```bash
   curl https://<DOMAIN>/api/projetos-overview
   ```
3. Frontend carrega: abrir `https://<DOMAIN>` no navegador.
4. Logs sem erro:
   ```bash
   journalctl -u <APP_NAME>-backend --since "10 min ago"
   sudo tail -f /var/log/nginx/error.log
   ```

---

## 10. Sintomas comuns e diagnóstico

| Sintoma | Causa provável | Verificar |
|---|---|---|
| `400 Bad Request` em todas as rotas | `ALLOWED_HOSTS` não contém o IP/domínio | `.env` |
| `502 Bad Gateway` no nginx | Gunicorn caído ou bind errado | `systemctl status`, `/etc/systemd/...` |
| `WORKER TIMEOUT` no log do Gunicorn | Latência atingiu `--timeout` | CPU da VM; considerar upgrade |
| Latência cresce com o tempo, RAM cresce sem soltar | `DEBUG=True` em produção | Variáveis carregadas pelo systemd |
| Frontend pisca mas API não responde | `VITE_API_URL` errado no build | Refazer com `/api` (caminho relativo) |
| `403 Forbidden` em arquivos do front | Permissões em `/var/www/<APP_NAME>` | `chown -R www-data:www-data` |

---

## 11. Referências internas

- Passo a passo prático de instalação: [`setup.md`](setup.md)
- Resultados dos testes de carga: [`loadtests/`](../loadtests/)
- Apresentação executiva: [`loadtests/apresentacao.html`](../loadtests/apresentacao.html)
- Locustfile (gerador de carga): [`locustfile.py`](../locustfile.py)
