# Setup da VM — Passo a passo

Roteiro linear para subir o ambiente do zero numa VM Ubuntu Server 24.
Premissas:

- VM já provisionada com IP fixo e acesso de rede.
- Postgres já instalado e acessível em `<POSTGRES_HOST>:<POSTGRES_PORT>`
  com `<DB_NAME>`, `<DB_USER>` e `<DB_PASSWORD>` criados.
- Você tem SSH na VM como `<APP_USER>`.

Para a arquitetura e dimensionamento (por quê desses parâmetros),
ver [`deploy.md`](deploy.md).

---

## 0. Placeholders usados

Substituir pelos valores reais antes de executar:

```
<APP_IP>           IP da VM             (ex: 192.168.56.10)
<APP_NAME>         Identificador        (ex: lunae)
<APP_USER>         Usuário Linux        (ex: lunae)
<BACKEND_PATH>     Path do backend      (ex: /opt/lunae/backend)
<POSTGRES_HOST>    Host do Postgres     (ex: 192.168.56.1)
<POSTGRES_PORT>    Porta do Postgres    (ex: 5432)
<DB_NAME>          Nome do banco        (ex: lunae)
<DB_USER>          Usuário do banco     (ex: fev-23)
<DB_PASSWORD>      Senha do banco       (gerada)
<SECRET_KEY>       Chave Django         (gerar 50+ chars aleatórios)
<WORKERS>          Workers do Gunicorn  (3 se 1 vCPU; 9 se 4 vCPUs)
```

---

## 1. Preparar a VM

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y \
    python3 python3-venv python3-pip \
    nginx \
    postgresql-client \
    git curl
```

Validar conectividade com o Postgres antes de seguir:

```bash
PGPASSWORD=<DB_PASSWORD> psql \
  -h <POSTGRES_HOST> -p <POSTGRES_PORT> \
  -U <DB_USER> -d <DB_NAME> -c "SELECT 1;"
```

Se der erro, **parar aqui** e resolver: rede, `pg_hba.conf`, firewall.
Detalhes em [`deploy.md`](deploy.md), seção de comunicação.

---

## 2. Transferir o backend para a VM

**No host (PowerShell)**, a partir da raiz do repositório:

```powershell
cd C:\caminho\para\repo

tar --exclude=API_5_SEM_BACK/.venv `
    --exclude=API_5_SEM_BACK/venv `
    --exclude=API_5_SEM_BACK/__pycache__ `
    --exclude=API_5_SEM_BACK/.git `
    --exclude=API_5_SEM_BACK/.pytest_cache `
    -czf api_back.tar.gz API_5_SEM_BACK

scp api_back.tar.gz <APP_USER>@<APP_IP>:~/
```

**Na VM:**

```bash
sudo mkdir -p <BACKEND_PATH>
sudo chown <APP_USER>:<APP_USER> <BACKEND_PATH>

cd <BACKEND_PATH>
tar -xzf ~/api_back.tar.gz --strip-components=1
```

---

## 3. Configurar Python e dependências

```bash
cd <BACKEND_PATH>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Criar o `.env`

```bash
cat > <BACKEND_PATH>/.env <<'EOF'
POSTGRES_DB=<DB_NAME>
POSTGRES_USER=<DB_USER>
POSTGRES_PASSWORD=<DB_PASSWORD>
POSTGRES_HOST=<POSTGRES_HOST>
POSTGRES_PORT=<POSTGRES_PORT>

SECRET_KEY=<SECRET_KEY>
DEBUG=False
ALLOWED_HOSTS=<APP_IP>,localhost,127.0.0.1
EOF

chmod 600 <BACKEND_PATH>/.env
```

> Substituir os placeholders no arquivo. O `chmod 600` impede que
> outros usuários da VM leiam a senha do banco.

---

## 5. Migrations e seed

```bash
cd <BACKEND_PATH>
source .venv/bin/activate
set -a; source .env; set +a

python manage.py migrate
python manage.py dev_db
```

`dev_db` popula o banco com dados de demonstração via `seed_0006`.

---

## 6. Gunicorn como serviço systemd

```bash
sudo tee /etc/systemd/system/<APP_NAME>-backend.service > /dev/null <<EOF
[Unit]
Description=<APP_NAME> backend (Gunicorn)
After=network.target

[Service]
Type=simple
User=<APP_USER>
WorkingDirectory=<BACKEND_PATH>
EnvironmentFile=<BACKEND_PATH>/.env
ExecStart=<BACKEND_PATH>/.venv/bin/gunicorn api.wsgi:application \\
    --bind 127.0.0.1:8000 \\
    --workers <WORKERS> \\
    --timeout 120 \\
    --access-logfile - \\
    --error-logfile -
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now <APP_NAME>-backend
sudo systemctl status <APP_NAME>-backend
```

Smoke test do backend (deve retornar JSON):

```bash
curl http://127.0.0.1:8000/api/projetos-overview
```

Acompanhar logs em outra aba se precisar:

```bash
journalctl -u <APP_NAME>-backend -f
```

---

## 7. Build do frontend (no host)

```powershell
cd C:\caminho\para\repo\API_5_SEM_FRONT
npm ci

$env:VITE_API_URL = "/api"
npm run build
```

> `VITE_API_URL=/api` faz o front bater na **mesma origem** que serviu
> o HTML. O nginx (próximo passo) cuida do proxy para o backend.

Mandar pra VM:

```powershell
scp -r dist <APP_USER>@<APP_IP>:/tmp/<APP_NAME>-dist
```

---

## 8. Instalar o frontend e configurar nginx

**Na VM:**

```bash
sudo mkdir -p /var/www/<APP_NAME>
sudo rm -rf /var/www/<APP_NAME>/*
sudo cp -r /tmp/<APP_NAME>-dist/* /var/www/<APP_NAME>/
sudo chown -R www-data:www-data /var/www/<APP_NAME>

sudo tee /etc/nginx/sites-available/<APP_NAME> > /dev/null <<'EOF'
server {
    listen 80 default_server;
    server_name _;

    root /var/www/<APP_NAME>;
    index index.html;

    # Frontend SPA — fallback pro index.html em rotas client-side
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend (loopback)
    location /api/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   Connection        "";
        proxy_read_timeout 120s;
    }
}
EOF

# Substituir <APP_NAME> no arquivo se o heredoc não tiver expandido:
sudo sed -i "s|<APP_NAME>|<APP_NAME>|g" /etc/nginx/sites-available/<APP_NAME>

sudo ln -sf /etc/nginx/sites-available/<APP_NAME> /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl reload nginx
```

> O heredoc com aspas simples (`<<'EOF'`) não expande variáveis,
> então os `<APP_NAME>` ficam literais — substituir manualmente ou
> rodar o `sed` acima com o valor correto nos dois lados.

---

## 9. Firewall

```bash
# Se ufw não estiver ativo:
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx HTTP'
sudo ufw --force enable
sudo ufw status
```

> A porta 8000 do Gunicorn **não** é aberta no firewall — backend
> escuta apenas em `127.0.0.1`, inacessível pela rede.

---

## 10. Smoke test end-to-end

**Na VM:**

```bash
curl -I http://127.0.0.1                    # nginx servindo o front
curl    http://127.0.0.1/api/projetos-overview   # API via nginx
```

**No host (navegador):**

```
http://<APP_IP>
```

- O dashboard precisa carregar.
- DevTools (F12) → Network → confirmar que requests `/api/...`
  retornam 200.

---

## 11. Atualizar o frontend depois (re-deploy)

Quando rebuildar o front:

```powershell
# host
cd API_5_SEM_FRONT
npm run build
scp -r dist <APP_USER>@<APP_IP>:/tmp/<APP_NAME>-dist
```

```bash
# VM
sudo rm -rf /var/www/<APP_NAME>/*
sudo cp -r /tmp/<APP_NAME>-dist/* /var/www/<APP_NAME>/
sudo chown -R www-data:www-data /var/www/<APP_NAME>
```

Nginx **não precisa de reload** — arquivos estáticos pegam na hora.
No navegador, `Ctrl+F5` ignora cache do browser.

---

## 12. Atualizar o backend depois (re-deploy)

```powershell
# host
scp api_back.tar.gz <APP_USER>@<APP_IP>:~/
```

```bash
# VM
cd <BACKEND_PATH>
tar -xzf ~/api_back.tar.gz --strip-components=1 --overwrite

source .venv/bin/activate
pip install -r requirements.txt   # se requirements mudaram
python manage.py migrate           # se houve nova migration

sudo systemctl restart <APP_NAME>-backend
sudo journalctl -u <APP_NAME>-backend -n 30 --no-pager
```

---

## 13. Validar capacidade com Locust (opcional)

A partir do host, depois que o sistema estiver no ar:

```powershell
cd C:\caminho\para\repo\API_5_SEM_BACK
pip install locust

locust -f locustfile.py `
  --host=http://<APP_IP> `
  --users 200 --spawn-rate 10 --run-time 5m `
  --headless --html relatorio.html --csv resultado
```

> Note o `--host` sem `:8000`: o teste passa pelo nginx, exatamente
> como um usuário real. Os endpoints `/api/...` do `locustfile.py`
> são proxiados automaticamente para o Gunicorn.
